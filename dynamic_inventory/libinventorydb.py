#!/usr/bin/env python3
"""Dataclasses and MySQL persistence for discovered inventory and host facts."""

from __future__ import annotations

import configparser
import ipaddress
import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import mysql.connector
from mysql.connector import Error as MySQLError
import yaml


LOG = logging.getLogger("inventory-db-loader")


@dataclass(frozen=True, slots=True)
class InventoryDatabaseConfig:
    host: str = "localhost"
    port: int = 3306
    user: str = "inventory"
    password: str = ""
    database: str = "inventory"
    connect_timeout: int = 10
    transaction_retries: int = 5
    retry_base_delay: float = 0.10

    @classmethod
    def from_ini(
        cls,
        filename: str | os.PathLike[str] = "/etc/inventory/inventory-db.ini",
        section: str = "mysql",
    ) -> "InventoryDatabaseConfig":
        parser = configparser.ConfigParser()
        parser.read(filename)
        values = parser[section] if parser.has_section(section) else {}

        return cls(
            host=os.getenv("INVENTORY_DB_HOST", values.get("host", cls.host)),
            port=int(os.getenv("INVENTORY_DB_PORT", values.get("port", str(cls.port)))),
            user=os.getenv("INVENTORY_DB_USER", values.get("user", cls.user)),
            password=os.getenv(
                "INVENTORY_DB_PASSWORD",
                values.get("password", cls.password),
            ),
            database=os.getenv(
                "INVENTORY_DB_NAME",
                values.get("database", cls.database),
            ),
            connect_timeout=int(os.getenv(
                "INVENTORY_DB_CONNECT_TIMEOUT",
                values.get("connect_timeout", str(cls.connect_timeout)),
            )),
            transaction_retries=int(os.getenv(
                "INVENTORY_DB_TRANSACTION_RETRIES",
                values.get("transaction_retries", str(cls.transaction_retries)),
            )),
            retry_base_delay=float(os.getenv(
                "INVENTORY_DB_RETRY_BASE_DELAY",
                values.get("retry_base_delay", str(cls.retry_base_delay)),
            )),
        )


@dataclass(frozen=True, slots=True)
class NetworkAddress:
    ip: str
    mac: str = ""


@dataclass(slots=True)
class HostFacts:
    hostname: str
    fqdn: str = ""
    os_distribution: str = ""
    os_major_version: str = ""
    os_minor_version: str = ""
    os_full_version: str = ""
    addresses: list[NetworkAddress] = field(default_factory=list)
    inventory_tags: list[str] = field(default_factory=list)
    source_file: str = ""
    raw_record: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml_file(cls, filename: str | os.PathLike[str]) -> "HostFacts":
        path = Path(filename)

        with path.open("r", encoding="utf-8") as stream:
            document = yaml.safe_load(stream)

        if not isinstance(document, dict):
            raise ValueError(f"{path}: top-level YAML value must be a mapping")

        hostname = str(document.get("hostname") or "").strip()
        fqdn = str(document.get("fqdn") or "").strip()

        if not hostname:
            hostname = fqdn.split(".", 1)[0] if fqdn else path.name

        os_info = document.get("os_info") or {}
        if not isinstance(os_info, dict):
            raise ValueError(f"{path}: os_info must be a mapping")

        raw_addresses = document.get("ip_mac_addresses") or []
        if not isinstance(raw_addresses, list):
            raise ValueError(f"{path}: ip_mac_addresses must be a list")

        addresses: list[NetworkAddress] = []
        seen_addresses: set[tuple[str, str]] = set()

        for item in raw_addresses:
            if not isinstance(item, dict):
                continue

            if "ip" in item or "mac" in item:
                ip = str(item.get("ip") or "").strip()
                mac = str(item.get("mac") or "").strip().lower()
            elif len(item) == 1:
                mac_value, ip_value = next(iter(item.items()))
                ip = str(ip_value or "").strip()
                mac = str(mac_value or "").strip().lower()
            else:
                continue

            if not ip:
                continue

            key = (ip, mac)
            if key in seen_addresses:
                continue

            seen_addresses.add(key)
            addresses.append(NetworkAddress(ip=ip, mac=mac))

        localroleinfo = str(document.get("localroleinfo") or "").strip()

        inventory_tags: list[str] = []
        seen_tags: set[str] = set()

        for raw_line in localroleinfo.splitlines():
            tag = raw_line.strip()
            if not tag or tag.startswith("#") or tag in seen_tags:
                continue
            seen_tags.add(tag)
            inventory_tags.append(tag)

        return cls(
            hostname=hostname,
            fqdn=fqdn,
            os_distribution=str(os_info.get("distribution") or "").strip(),
            os_major_version=str(os_info.get("major_version") or "").strip(),
            os_minor_version=str(os_info.get("minor_version") or "").strip(),
            os_full_version=str(os_info.get("full_version") or "").strip(),
            addresses=addresses,
            inventory_tags=inventory_tags,
            source_file=path.name,
            raw_record=document,
        )

    def as_json(self) -> str:
        return json.dumps(
            self.raw_record,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )


def read_inventory_ips(filename: str | os.PathLike[str]) -> list[str]:
    path = Path(filename)
    addresses: list[str] = []
    seen: set[str] = set()

    with path.open("r", encoding="utf-8") as stream:
        for raw_line in stream:
            line = raw_line.strip()

            if not line or line.startswith("#") or line.startswith(";"):
                continue
            if line.startswith("[") and line.endswith("]"):
                continue

            token = line.split()[0]

            try:
                address = ipaddress.ip_address(token)
            except ValueError:
                continue

            if address.version != 4:
                continue

            ip = str(address)
            if ip not in seen:
                seen.add(ip)
                addresses.append(ip)

    return addresses


@dataclass(slots=True)
class InventoryFactStore:
    config: InventoryDatabaseConfig

    RETRYABLE_MYSQL_ERRORS = frozenset({
        1205,  # Lock wait timeout exceeded
        1213,  # Deadlock found when trying to get lock
    })

    def _connect(self):
        return mysql.connector.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database,
            connection_timeout=self.config.connect_timeout,
            autocommit=False,
        )

    def begin_discovery_run(
        self,
        discovered_ips: Iterable[str],
        source: str = "nmap",
    ) -> int:
        ips = sorted(set(discovered_ips), key=ipaddress.ip_address)

        conn = self._connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE inventory_discovery SET currently_discovered = 0"
            )

            for ip in ips:
                cursor.execute(
                    """
                    INSERT INTO inventory_discovery (
                        ipv4_address,
                        discovery_source,
                        currently_discovered,
                        facts_available,
                        first_seen,
                        last_seen
                    )
                    VALUES (
                        %s, %s, 1, 0,
                        CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP
                    )
                    ON DUPLICATE KEY UPDATE
                        discovery_source = VALUES(discovery_source),
                        currently_discovered = 1,
                        facts_available = 0,
                        last_seen = CURRENT_TIMESTAMP
                    """,
                    (ip, source),
                )

            conn.commit()
            return len(ips)

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    def _store_host_once(self, host: HostFacts) -> int:
        conn = self._connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO inventory_hosts (
                    hostname,
                    fqdn,
                    os_distribution,
                    os_major_version,
                    os_minor_version,
                    os_full_version,
                    source_file,
                    facts_json,
                    last_seen
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    CURRENT_TIMESTAMP
                )
                ON DUPLICATE KEY UPDATE
                    fqdn = VALUES(fqdn),
                    os_distribution = VALUES(os_distribution),
                    os_major_version = VALUES(os_major_version),
                    os_minor_version = VALUES(os_minor_version),
                    os_full_version = VALUES(os_full_version),
                    source_file = VALUES(source_file),
                    facts_json = VALUES(facts_json),
                    last_seen = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    host.hostname,
                    host.fqdn or None,
                    host.os_distribution or None,
                    host.os_major_version or None,
                    host.os_minor_version or None,
                    host.os_full_version or None,
                    host.source_file or None,
                    host.as_json(),
                ),
            )

            cursor.execute(
                "SELECT id FROM inventory_hosts WHERE hostname = %s",
                (host.hostname,),
            )
            row = cursor.fetchone()

            if not row:
                raise RuntimeError(
                    f"Unable to resolve database ID for {host.hostname}"
                )

            host_id = int(row[0])

            cursor.execute(
                "DELETE FROM inventory_addresses WHERE host_id = %s",
                (host_id,),
            )

            ordered_addresses = sorted(
                host.addresses,
                key=lambda item: (ipaddress.ip_address(item.ip), item.mac),
            )

            for address in ordered_addresses:
                cursor.execute(
                    """
                    INSERT INTO inventory_addresses (
                        host_id,
                        ipv4_address,
                        mac_address
                    )
                    VALUES (%s, %s, %s)
                    """,
                    (
                        host_id,
                        address.ip,
                        address.mac or None,
                    ),
                )

                cursor.execute(
                    """
                    INSERT INTO inventory_discovery (
                        ipv4_address,
                        host_id,
                        discovery_source,
                        currently_discovered,
                        facts_available,
                        first_seen,
                        last_seen
                    )
                    VALUES (
                        %s, %s, 'ansible-facts', 0, 1,
                        CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP
                    )
                    ON DUPLICATE KEY UPDATE
                        host_id = VALUES(host_id),
                        facts_available = 1
                    """,
                    (address.ip, host_id),
                )

            cursor.execute(
                "DELETE FROM inventory_host_tags WHERE host_id = %s",
                (host_id,),
            )

            for tag in sorted(host.inventory_tags):
                cursor.execute(
                    """
                    INSERT IGNORE INTO inventory_tags (tag_name)
                    VALUES (%s)
                    """,
                    (tag,),
                )

                cursor.execute(
                    "SELECT id FROM inventory_tags WHERE tag_name = %s",
                    (tag,),
                )
                tag_row = cursor.fetchone()

                if not tag_row:
                    raise RuntimeError(
                        f"Unable to resolve inventory tag ID: {tag}"
                    )

                cursor.execute(
                    """
                    INSERT INTO inventory_host_tags (host_id, tag_id)
                    VALUES (%s, %s)
                    """,
                    (host_id, int(tag_row[0])),
                )

            conn.commit()
            return host_id

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    def store_host(self, host: HostFacts) -> int:
        attempts = self.config.transaction_retries + 1

        for attempt in range(1, attempts + 1):
            try:
                return self._store_host_once(host)

            except MySQLError as exc:
                if (
                    exc.errno not in self.RETRYABLE_MYSQL_ERRORS
                    or attempt >= attempts
                ):
                    raise

                delay = (
                    self.config.retry_base_delay
                    * (2 ** (attempt - 1))
                    + random.uniform(0, self.config.retry_base_delay)
                )

                LOG.warning(
                    "Retrying %-30s after MySQL %s "
                    "(attempt %d/%d, %.3fs)",
                    host.hostname,
                    exc.errno,
                    attempt + 1,
                    attempts,
                    delay,
                )

                time.sleep(delay)

        raise RuntimeError(
            f"Transaction retry loop exhausted for {host.hostname}"
        )

    def store_yaml_file(
        self,
        filename: str | os.PathLike[str],
    ) -> tuple[int, HostFacts]:
        host = HostFacts.from_yaml_file(filename)
        host_id = self.store_host(host)
        return host_id, host
 
