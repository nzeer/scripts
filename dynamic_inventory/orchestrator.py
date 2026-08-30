#!/usr/bin/env python3

"""
Inventory generation orchestrator.

Pipeline:

    scan.py
        |
        v
    ./json_hosts_data/*.json
        |
        v
    json2yaml.py
        |
        v
    ./inventory
        |
        v
    gather_facts.yml
        |
        v
    ./hosts/*.yaml
        |
        +---------------------------+
        |                           |
        v                           v
    parse.py                load_inventory_db.py
                                    |
                                    v
                              MySQL summary


Failure semantics:

    scan.py failure              -> STOP
    json2yaml.py failure         -> STOP
    gather_facts.yml nonzero     -> WARN and CONTINUE
    parse.py failure             -> ERROR
    database loader failure      -> ERROR
    database summary failure     -> WARN

The Ansible fact-gathering stage is intentionally non-fatal because
network discovery may identify live IP addresses that do not run SSH
or cannot be accessed by the Ansible runner account.
"""

from __future__ import annotations

import argparse
import configparser
import fcntl
import json
import logging
import os
import subprocess
import sys
import time

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import mysql.connector


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

SCAN_SCRIPT = BASE_DIR / "scan.py"
JSON2YAML_SCRIPT = BASE_DIR / "json2yaml.py"
FACTS_PLAYBOOK = BASE_DIR / "gather_facts.yml"
PARSE_SCRIPT = BASE_DIR / "parse.py"
DB_LOADER_SCRIPT = BASE_DIR / "load_inventory_db.py"

NMAP_DIR = BASE_DIR / "nmap"
JSON_HOSTS_DIR = BASE_DIR / "json_hosts_data"
INVENTORY_FILE = BASE_DIR / "inventory"
HOST_FACTS_DIR = BASE_DIR / "hosts"

DB_CONFIG_FILE = BASE_DIR / "inventory-db.ini"
DB_WORKERS = 10

LOCK_FILE = BASE_DIR / ".inventory-orchestrator.lock"


# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

#
# Change this path to place inventory-generation logs wherever desired.
#
# The complete directory hierarchy will be created automatically
# at runtime if it does not already exist.
#
LOG_DIRECTORY = Path("./log")

#
# Produces filenames such as:
#
#     05252026-inventory-generation.log
#
LOG_DATE_FORMAT = "%m%d%Y"


# ---------------------------------------------------------------------------
# Scan synchronization
# ---------------------------------------------------------------------------

#
# Maximum amount of time to wait for all nmap JSON output files.
#
SCAN_WAIT_TIMEOUT = 1800

#
# Number of seconds between output checks.
#
SCAN_POLL_INTERVAL = 2

#
# Number of consecutive checks during which the JSON files must
# remain unchanged before discovery is considered complete.
#
SCAN_STABLE_CHECKS = 3


PYTHON = sys.executable


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger("inventory_orchestrator")


def configure_logging(verbose: bool = False) -> Path:
    """
    Configure console and file logging.

    The configured logging directory and all missing parent
    directories are created automatically.

    Log filename format:

        MMDDYYYY-inventory-generation.log

    Example:

        05252026-inventory-generation.log
    """

    level = logging.DEBUG if verbose else logging.INFO

    #
    # Create the complete logging directory hierarchy.
    #
    try:
        LOG_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

    except OSError as exc:
        raise RuntimeError(
            f"Unable to create logging directory "
            f"{LOG_DIRECTORY}: {exc}"
        ) from exc

    log_date = time.strftime(
        LOG_DATE_FORMAT
    )

    log_file = (
        LOG_DIRECTORY
        / f"{log_date}-inventory-generation.log"
    )

    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    try:
        file_handler = logging.FileHandler(
            log_file
        )

    except OSError as exc:
        raise RuntimeError(
            f"Unable to open log file "
            f"{log_file}: {exc}"
        ) from exc

    file_handler.setFormatter(formatter)

    #
    # File logging always receives DEBUG and above.
    #
    file_handler.setLevel(logging.DEBUG)

    logger.handlers.clear()
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return log_file


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class StageResult:
    name: str
    command: list[str]
    returncode: int
    duration: float

    @property
    def success(self) -> bool:
        return self.returncode == 0


@dataclass
class InventoryStats:
    discovered_json_files: int = 0
    inventory_ips: int = 0
    fact_files: int = 0


@dataclass
class DatabaseStats:
    discovered: int = 0
    with_facts: int = 0
    discovery_only: int = 0


# ---------------------------------------------------------------------------
# Locking
# ---------------------------------------------------------------------------

class ProcessLock:

    def __init__(self, path: Path):
        self.path = path
        self.handle = None

    def __enter__(self):

        self.handle = open(
            self.path,
            "w",
        )

        try:
            fcntl.flock(
                self.handle.fileno(),
                fcntl.LOCK_EX | fcntl.LOCK_NB,
            )

        except BlockingIOError:

            logger.error(
                "Another inventory generation process "
                "is already running."
            )

            raise RuntimeError(
                "orchestrator already running"
            )

        self.handle.write(
            str(os.getpid())
        )

        self.handle.flush()

        logger.debug(
            "Acquired orchestrator lock: %s",
            self.path,
        )

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):

        if self.handle:

            fcntl.flock(
                self.handle.fileno(),
                fcntl.LOCK_UN,
            )

            self.handle.close()

        try:

            self.path.unlink(
                missing_ok=True
            )

        except OSError:
            pass

        logger.debug(
            "Released orchestrator lock."
        )


# ---------------------------------------------------------------------------
# Command execution
# ---------------------------------------------------------------------------

def run_command(
    name: str,
    command: list[str],
    fatal: bool = True,
) -> StageResult:

    logger.info(
        "=" * 72
    )

    logger.info(
        "Starting stage: %s",
        name,
    )

    logger.info(
        "Command: %s",
        " ".join(command),
    )

    start = time.monotonic()

    try:

        result = subprocess.run(
            command,
            cwd=BASE_DIR,
        )

    except OSError as exc:

        logger.exception(
            "Unable to execute stage '%s': %s",
            name,
            exc,
        )

        raise RuntimeError(
            f"Unable to execute {name}"
        ) from exc

    duration = (
        time.monotonic() - start
    )

    stage = StageResult(
        name=name,
        command=command,
        returncode=result.returncode,
        duration=duration,
    )

    if stage.success:

        logger.info(
            "Completed stage: %s "
            "[rc=%d, %.2fs]",
            name,
            stage.returncode,
            stage.duration,
        )

    elif fatal:

        logger.error(
            "Stage failed: %s "
            "[rc=%d, %.2fs]",
            name,
            stage.returncode,
            stage.duration,
        )

        raise RuntimeError(
            f"{name} failed with "
            f"rc={stage.returncode}"
        )

    else:

        logger.warning(
            "Stage returned non-zero: %s "
            "[rc=%d, %.2fs] -- continuing",
            name,
            stage.returncode,
            stage.duration,
        )

    return stage


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_required_files() -> None:

    required = [
        SCAN_SCRIPT,
        JSON2YAML_SCRIPT,
        FACTS_PLAYBOOK,
        PARSE_SCRIPT,
        DB_LOADER_SCRIPT,
        DB_CONFIG_FILE,
    ]

    missing = [
        path
        for path in required
        if not path.exists()
    ]

    if missing:

        for path in missing:

            logger.error(
                "Required file not found: %s",
                path,
            )

        raise RuntimeError(
            "One or more required pipeline "
            "files are missing."
        )


def wait_for_scan_output(
    timeout: int = SCAN_WAIT_TIMEOUT,
    poll_interval: int = SCAN_POLL_INTERVAL,
    stable_checks: int = SCAN_STABLE_CHECKS,
) -> int:
    """
    Wait until every configured nmap plugin has produced a complete,
    stable, valid JSON output file.

    The expected output count is derived from:

        ./nmap/*-nmap.yaml

    A result set is considered complete when:

      - the number of *-hosts.json files matches the number of plugins
      - every JSON file parses successfully
      - file sizes remain unchanged for several consecutive checks
    """

    plugin_files = sorted(
        NMAP_DIR.glob(
            "*-nmap.yaml"
        )
    )

    expected_count = len(
        plugin_files
    )

    if expected_count == 0:

        raise RuntimeError(
            f"No nmap plugin files found "
            f"in {NMAP_DIR}"
        )

    logger.info(
        "Waiting for %d nmap "
        "scan result file(s).",
        expected_count,
    )

    deadline = (
        time.monotonic()
        + timeout
    )

    previous_sizes: dict[
        Path,
        int,
    ] = {}

    stable_count = 0

    while (
        time.monotonic()
        < deadline
    ):

        json_files = sorted(
            JSON_HOSTS_DIR.glob(
                "*-hosts.json"
            )
        )

        if (
            len(json_files)
            != expected_count
        ):

            logger.info(
                "Discovery progress: "
                "%d/%d JSON result file(s)",
                len(json_files),
                expected_count,
            )

            stable_count = 0
            previous_sizes = {}

            time.sleep(
                poll_interval
            )

            continue

        all_valid = True

        for path in json_files:

            try:

                with path.open(
                    "r"
                ) as handle:

                    json.load(
                        handle
                    )

            except (
                json.JSONDecodeError,
                OSError,
            ):

                logger.debug(
                    "Discovery file is "
                    "not complete yet: %s",
                    path,
                )

                all_valid = False

                break

        if not all_valid:

            stable_count = 0
            previous_sizes = {}

            time.sleep(
                poll_interval
            )

            continue

        current_sizes = {
            path: path.stat().st_size
            for path in json_files
        }

        if (
            current_sizes
            == previous_sizes
        ):

            stable_count += 1

        else:

            stable_count = 0
            previous_sizes = (
                current_sizes
            )

        if (
            stable_count
            >= stable_checks
        ):

            logger.info(
                "Discovery complete: "
                "%d/%d scan results are "
                "present, valid, and stable.",
                len(json_files),
                expected_count,
            )

            return len(
                json_files
            )

        logger.debug(
            "Waiting for discovery "
            "files to stabilize "
            "(%d/%d checks).",
            stable_count,
            stable_checks,
        )

        time.sleep(
            poll_interval
        )

    raise RuntimeError(
        "Timed out waiting for nmap "
        "discovery to complete. "
        f"Expected {expected_count} "
        "result file(s)."
    )


def count_inventory_ips() -> int:

    if not INVENTORY_FILE.exists():

        raise RuntimeError(
            f"Inventory file not found: "
            f"{INVENTORY_FILE}"
        )

    count = 0
    in_devices = False

    with INVENTORY_FILE.open() as handle:

        for raw_line in handle:

            line = (
                raw_line.strip()
            )

            if not line:
                continue

            if (
                line.startswith("[")
                and line.endswith("]")
            ):

                in_devices = (
                    line == "[devices]"
                )

                continue

            if in_devices:
                count += 1

    if count == 0:

        raise RuntimeError(
            "Generated inventory contains "
            "no hosts in [devices]."
        )

    logger.info(
        "Generated discovery inventory "
        "contains %d IP address(es).",
        count,
    )

    return count


def count_fact_files() -> int:

    if not HOST_FACTS_DIR.exists():

        logger.warning(
            "Host facts directory "
            "does not exist: %s",
            HOST_FACTS_DIR,
        )

        return 0

    files = [
        path
        for path
        in HOST_FACTS_DIR.iterdir()
        if path.is_file()
    ]

    return len(files)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def load_database_config() -> dict:

    config = (
        configparser.ConfigParser()
    )

    if not config.read(
        DB_CONFIG_FILE
    ):

        raise RuntimeError(
            f"Unable to read database "
            f"config: {DB_CONFIG_FILE}"
        )

    section_name = "mysql"

    if section_name not in config:

        raise RuntimeError(
            f"Database config is missing "
            f"[{section_name}] section."
        )

    section = config[
        section_name
    ]

    required = [
        "host",
        "user",
        "password",
        "database",
    ]

    missing = [
        key
        for key in required
        if not section.get(key)
    ]

    if missing:

        raise RuntimeError(
            "Database configuration "
            "is missing: "
            + ", ".join(missing)
        )

    return {
        "host": section.get(
            "host"
        ),
        "port": section.getint(
            "port",
            fallback=3306,
        ),
        "user": section.get(
            "user"
        ),
        "password": section.get(
            "password"
        ),
        "database": section.get(
            "database"
        ),
    }


def get_database_stats() -> DatabaseStats:

    logger.info(
        "=" * 72
    )

    logger.info(
        "Querying database "
        "inventory statistics."
    )

    db_config = (
        load_database_config()
    )

    connection = None
    cursor = None

    try:

        connection = (
            mysql.connector.connect(
                **db_config
            )
        )

        cursor = (
            connection.cursor()
        )

        cursor.execute(
            """
            SELECT
                COUNT(*) AS discovered,
                COALESCE(
                    SUM(facts_available = 1),
                    0
                ) AS with_facts,
                COALESCE(
                    SUM(facts_available = 0),
                    0
                ) AS discovery_only
            FROM inventory_discovery
            WHERE currently_discovered = 1
            """
        )

        row = (
            cursor.fetchone()
        )

        if row is None:
            return DatabaseStats()

        stats = DatabaseStats(
            discovered=int(
                row[0] or 0
            ),
            with_facts=int(
                row[1] or 0
            ),
            discovery_only=int(
                row[2] or 0
            ),
        )

        logger.info(
            "Database discovery statistics: "
            "discovered=%d, "
            "with_facts=%d, "
            "discovery_only=%d",
            stats.discovered,
            stats.with_facts,
            stats.discovery_only,
        )

        return stats

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ---------------------------------------------------------------------------
# Pipeline stages
# ---------------------------------------------------------------------------

def run_discovery(
    stats: InventoryStats,
) -> StageResult:

    result = run_command(
        name="Network discovery",
        command=[
            PYTHON,
            str(SCAN_SCRIPT),
        ],
        fatal=True,
    )

    #
    # Explicit discovery barrier.
    #
    # Do not proceed merely because scan.py returned.
    # Every configured nmap plugin must have produced
    # a complete and stable JSON result.
    #
    stats.discovered_json_files = (
        wait_for_scan_output()
    )

    return result


def build_inventory(
    stats: InventoryStats,
) -> StageResult:

    result = run_command(
        name="Build discovery inventory",
        command=[
            PYTHON,
            str(JSON2YAML_SCRIPT),
        ],
        fatal=True,
    )

    stats.inventory_ips = (
        count_inventory_ips()
    )

    return result


def gather_facts(
    stats: InventoryStats,
) -> StageResult:

    result = run_command(
        name="Gather host facts",
        command=[
            "ansible-playbook",
            "-i",
            str(INVENTORY_FILE),
            str(FACTS_PLAYBOOK),
        ],
        fatal=False,
    )

    stats.fact_files = (
        count_fact_files()
    )

    logger.info(
        "Fact collection produced "
        "%d fact file(s).",
        stats.fact_files,
    )

    if not result.success:

        logger.warning(
            "Ansible returned rc=%d. "
            "This does not automatically "
            "indicate inventory generation "
            "failure because some discovered "
            "hosts may be unreachable or "
            "may not provide SSH.",
            result.returncode,
        )

    return result


# ---------------------------------------------------------------------------
# Publish
# ---------------------------------------------------------------------------

def run_parse() -> StageResult:

    return run_command(
        name="Generate Ansible inventory",
        command=[
            PYTHON,
            str(PARSE_SCRIPT),
        ],
        fatal=False,
    )


def run_database_loader() -> StageResult:

    return run_command(
        name="Load inventory database",
        command=[
            PYTHON,
            str(DB_LOADER_SCRIPT),

            "--inventory",
            str(INVENTORY_FILE),

            "--facts-dir",
            str(HOST_FACTS_DIR),

            "--config",
            str(DB_CONFIG_FILE),

            "--workers",
            str(DB_WORKERS),
        ],
        fatal=False,
    )


def publish_results() -> dict[
    str,
    StageResult,
]:

    logger.info(
        "=" * 72
    )

    logger.info(
        "Starting publish stages "
        "in parallel."
    )

    results: dict[
        str,
        StageResult,
    ] = {}

    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        future_map = {

            executor.submit(
                run_parse
            ): (
                "Generate Ansible inventory"
            ),

            executor.submit(
                run_database_loader
            ): (
                "Load inventory database"
            ),
        }

        for future in as_completed(
            future_map
        ):

            name = (
                future_map[future]
            )

            try:

                results[name] = (
                    future.result()
                )

            except Exception:

                logger.exception(
                    "Unexpected failure "
                    "during publish stage: %s",
                    name,
                )

                results[name] = (
                    StageResult(
                        name=name,
                        command=[],
                        returncode=255,
                        duration=0.0,
                    )
                )

    return results


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(
    stats: InventoryStats,
    database_stats: DatabaseStats | None,
    facts_result: StageResult,
    publish_results_map:
        dict[str, StageResult],
    total_duration: float,
) -> None:

    logger.info(
        "=" * 72
    )

    logger.info(
        "Inventory generation summary"
    )

    logger.info(
        "=" * 72
    )

    logger.info(
        "Discovery JSON files : %d",
        stats.discovered_json_files,
    )

    logger.info(
        "Inventory IPs        : %d",
        stats.inventory_ips,
    )

    logger.info(
        "Fact files created   : %d",
        stats.fact_files,
    )

    logger.info(
        "Ansible return code  : %d",
        facts_result.returncode,
    )

    if database_stats is not None:

        logger.info(
            "-" * 72
        )

        logger.info(
            "DB discovered IPs  : %d",
            database_stats.discovered,
        )

        logger.info(
            "DB with facts      : %d",
            database_stats.with_facts,
        )

        logger.info(
            "DB discovery-only  : %d",
            database_stats.discovery_only,
        )

        if (
            database_stats.discovered
            != stats.inventory_ips
        ):

            logger.warning(
                "Inventory/database count "
                "mismatch: inventory=%d "
                "database=%d",
                stats.inventory_ips,
                database_stats.discovered,
            )

    logger.info(
        "-" * 72
    )

    for (
        name,
        result,
    ) in publish_results_map.items():

        logger.info(
            "%-24s: rc=%d",
            name,
            result.returncode,
        )

    logger.info(
        "Total runtime        : %.2fs",
        total_duration,
    )

    logger.info(
        "=" * 72
    )


# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------

def parse_arguments() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Run network discovery, "
            "build the temporary inventory, "
            "gather host facts, generate "
            "the production inventory, and "
            "load the inventory database."
        )
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:

    args = parse_arguments()

    #
    # Logging is initialized before any inventory work begins.
    # Failure to create/open the logging path is fatal.
    #
    try:

        log_file = configure_logging(
            verbose=args.verbose
        )

    except RuntimeError as exc:

        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )

        return 1

    total_start = (
        time.monotonic()
    )

    stats = InventoryStats()
    database_stats = None

    logger.info(
        "=" * 72
    )

    logger.info(
        "Starting inventory generation"
    )

    logger.info(
        "Working directory: %s",
        BASE_DIR,
    )

    logger.info(
        "Log directory: %s",
        LOG_DIRECTORY,
    )

    logger.info(
        "Log file: %s",
        log_file,
    )

    try:

        with ProcessLock(
            LOCK_FILE
        ):

            validate_required_files()

            #
            # Stage 1
            #
            run_discovery(
                stats
            )

            #
            # Stage 2
            #
            build_inventory(
                stats
            )

            #
            # Stage 3
            #
            facts_result = (
                gather_facts(
                    stats
                )
            )

            #
            # Stage 4
            #
            publish_result_map = (
                publish_results()
            )

            #
            # Database statistics are only
            # authoritative after the loader
            # completed successfully.
            #
            db_result = (
                publish_result_map.get(
                    "Load inventory database"
                )
            )

            if (
                db_result is not None
                and db_result.success
            ):

                try:

                    database_stats = (
                        get_database_stats()
                    )

                except Exception:

                    logger.exception(
                        "Unable to query "
                        "database summary "
                        "statistics."
                    )

            total_duration = (
                time.monotonic()
                - total_start
            )

            print_summary(
                stats=stats,
                database_stats=(
                    database_stats
                ),
                facts_result=(
                    facts_result
                ),
                publish_results_map=(
                    publish_result_map
                ),
                total_duration=(
                    total_duration
                ),
            )

            #
            # The Ansible fact-gathering
            # return code intentionally does
            # NOT determine overall success.
            #
            publish_failed = any(
                not result.success
                for result
                in publish_result_map.values()
            )

            if publish_failed:

                logger.error(
                    "Inventory generation "
                    "completed with "
                    "publish errors."
                )

                return 1

            logger.info(
                "Inventory generation "
                "completed successfully."
            )

            return 0

    except RuntimeError as exc:

        logger.error(
            "Inventory generation "
            "aborted: %s",
            exc,
        )

        return 1

    except KeyboardInterrupt:

        logger.warning(
            "Inventory generation "
            "interrupted."
        )

        return 130

    except Exception:

        logger.exception(
            "Unexpected orchestrator "
            "failure."
        )

        return 1


if __name__ == "__main__":
    sys.exit(
        main()
    )

 
