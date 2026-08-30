#!/usr/bin/env python3
"""Load lightweight discovery plus available host facts into MySQL."""

from __future__ import annotations

import argparse
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from libinventorydb import (
    HostFacts,
    InventoryDatabaseConfig,
    InventoryFactStore,
    read_inventory_ips,
)


LOG = logging.getLogger("inventory-db-loader")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--inventory",
        default="./inventory",
        help="Generated Ansible inventory (default: ./inventory)",
    )
    parser.add_argument(
        "--facts-dir",
        default="./hosts",
        help="Gathered fact directory (default: ./hosts)",
    )
    parser.add_argument(
        "--config",
        default="/etc/inventory/inventory-db.ini",
        help="MySQL configuration file",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Parallel fact loader workers (default: 10)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse discovery and fact files without touching MySQL",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


def discover_fact_files(facts_dir: Path) -> list[Path]:
    if not facts_dir.is_dir():
        return []

    return sorted(
        (
            path
            for path in facts_dir.iterdir()
            if path.is_file() and not path.name.startswith(".")
        ),
        key=lambda path: path.name.lower(),
    )


def validate_one(filename: Path) -> tuple[Path, HostFacts]:
    return filename, HostFacts.from_yaml_file(filename)


def load_one(
    filename: Path,
    config: InventoryDatabaseConfig,
) -> tuple[Path, int, HostFacts]:
    store = InventoryFactStore(config)
    host_id, host = store.store_yaml_file(filename)
    return filename, host_id, host


def main() -> int:
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    inventory_file = Path(args.inventory).resolve()
    facts_dir = Path(args.facts_dir).resolve()

    if not inventory_file.is_file():
        LOG.error("Generated inventory does not exist: %s", inventory_file)
        return 1

    if args.workers < 1:
        LOG.error("--workers must be at least 1")
        return 1

    try:
        discovered_ips = read_inventory_ips(inventory_file)
    except Exception as exc:
        LOG.error("Unable to parse %s: %s", inventory_file, exc)
        return 1

    fact_files = discover_fact_files(facts_dir)

    LOG.info(
        "Discovery: %d IP(s) from %s",
        len(discovered_ips),
        inventory_file,
    )
    LOG.info(
        "Facts: %d file(s) from %s",
        len(fact_files),
        facts_dir,
    )

    if args.dry_run:
        LOG.info("Dry-run mode: MySQL will not be contacted")
    else:
        config = InventoryDatabaseConfig.from_ini(args.config)
        store = InventoryFactStore(config)

        LOG.info(
            "Database target: %s:%d/%s",
            config.host,
            config.port,
            config.database,
        )
        LOG.info(
            "Transaction retries: %d, base delay: %.3fs",
            config.transaction_retries,
            config.retry_base_delay,
        )

        count = store.begin_discovery_run(
            discovered_ips,
            source="nmap",
        )
        LOG.info("Stored/refreshed %d discovery row(s)", count)

    successes = 0
    failures = 0

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        if args.dry_run:
            future_map = {
                executor.submit(validate_one, filename): filename
                for filename in fact_files
            }
        else:
            future_map = {
                executor.submit(load_one, filename, config): filename
                for filename in fact_files
            }

        for future in as_completed(future_map):
            filename = future_map[future]

            try:
                result = future.result()

                if args.dry_run:
                    _, host = result
                    LOG.info(
                        "Validated %-30s host=%s ips=%d tags=%d",
                        filename.name,
                        host.hostname,
                        len(host.addresses),
                        len(host.inventory_tags),
                    )
                else:
                    _, host_id, host = result
                    LOG.info(
                        "Loaded %-30s host_id=%d ips=%d tags=%d",
                        host.hostname,
                        host_id,
                        len(host.addresses),
                        len(host.inventory_tags),
                    )

                successes += 1

            except Exception as exc:
                failures += 1
                LOG.error("Failed %-30s %s", filename.name, exc)

    LOG.info(
        "Completed: discovery=%d facts_loaded=%d facts_failed=%d",
        len(discovered_ips),
        successes,
        failures,
    )

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
 
