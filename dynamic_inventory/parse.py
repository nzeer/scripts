#!/usr/bin/env python3
"""Generate Ansible inventories from gather_facts.yml host records."""
from __future__ import annotations
import json
import os
import pathlib as p
import re
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Set
import yaml
from libcommon import clone_everything, delete_directory, get_timestamp, glob_files, merge_files, write_file
from libhostinfo import HostInfo
from libhumangroupinfo import HumanGroupLookup
from libinventoryinfo import Inventory, InventoryEntry
DEBUG = True
PARSER_VERSION = "2026-07-10-humangroup-dataclass-v6"

#GLOBAL_STATIC_COPY_DIRECTORY = "/home/rjackson/dynamic_inventory_live/static"
#GLOBAL_HOSTS_INFO_DIRECTORY = "/home/rjackson/dynamic_inventory_live/hosts"
#GLOBAL_INVENTORY_DIRECTORY = "/ansible/inventory"
#GLOBAL_HOSTS_CSV = "/ansible/csv/hosts.csv"
GLOBAL_STATIC_COPY_DIRECTORY = "/home/rjackson/dynamic_inventory_live_dev/static"
GLOBAL_HOSTS_INFO_DIRECTORY = "/home/rjackson/dynamic_inventory_live_dev/hosts"
GLOBAL_INVENTORY_DIRECTORY = "/home/rjackson/dynamic_inventory_live_dev/ansible/inventory"
GLOBAL_HOSTS_CSV = "/home/rjackson/dynamic_inventory_live_dev/ansible/csv/hosts.csv"


# Centralized /etc/humangroups taxonomy and parsing rules.
HUMAN_GROUP_LOOKUP = HumanGroupLookup()

def debug(message: str) -> None:
    if DEBUG:
        print(f"[{get_timestamp()}] {message}")

def sanitize_group_name(value: str) -> str:
    """Convert arbitrary text into an Ansible-safe group name."""
    return HUMAN_GROUP_LOOKUP.sanitize_group_name(value)

def derive_localrole_groups(localroleinfo: str) -> List[str]:
    """Return all normalized Ansible groups derived from /etc/humangroups."""
    parsed = HUMAN_GROUP_LOOKUP.parse(localroleinfo)
    if DEBUG and parsed.unmatched_lines:
        for line in parsed.unmatched_lines:
            debug(f"ignoring unrecognized humangroups line: {line}")
    return parsed.all_groups()
def host_from_record(record: Dict[str, Any]) -> HostInfo:
    if not isinstance(record, dict):
        raise ValueError("host record must be a mapping")
    fqdn = str(record.get("fqdn") or record.get("hostname") or "").strip()
    hostname = str(record.get("hostname") or fqdn.split(".", 1)[0]).strip()
    os_info = record.get("os_info") or {}
    ip_mac_addresses = record.get("ip_mac_addresses") or []
    localroleinfo = str(record.get("localroleinfo") or "").strip()
    if not fqdn:
        raise ValueError("host record is missing fqdn/hostname")
    if not isinstance(os_info, dict):
        raise ValueError(f"host {hostname}: os_info must be a mapping")
    if not isinstance(ip_mac_addresses, list):
        raise ValueError(f"host {hostname}: ip_mac_addresses must be a list")
    return HostInfo(
        name=fqdn,
        hostname=hostname,
        ip_mac_addresses=ip_mac_addresses,
        os_info=os_info,
        localroleinfo=localroleinfo,
        localrole_groups=derive_localrole_groups(localroleinfo),
    )

def load_host(file_host: os.PathLike | str) -> HostInfo:
    """Load one YAML host record written by gather_facts.yml."""
    path = p.Path(file_host)
    if not path.is_file():
        raise RuntimeError(f"file does not exist: {path}")
    debug(f"reading YAML host file: {path}")
    with path.open("r", encoding="utf-8") as stream:
        record = yaml.safe_load(stream)
    return host_from_record(record)

def load_hosts(directory_hosts_data: os.PathLike | str) -> List[HostInfo]:
    """Load all non-hidden YAML host records from a directory."""
    directory = p.Path(directory_hosts_data)
    if not directory.is_dir():
        raise RuntimeError(f"directory does not exist: {directory}")
    hosts: List[HostInfo] = []
    for file_path in sorted(path for path in directory.iterdir() if path.is_file() and not path.name.startswith(".")):
        try:
            hosts.append(load_host(file_path))
        except (OSError, ValueError, yaml.YAMLError) as exc:
            print(f"[{get_timestamp()}] skipping {file_path}: {exc}")
    return hosts

def load_hosts_jsonl(file_hosts_jsonl: os.PathLike | str) -> List[HostInfo]:
    """Load the master JSON-lines file (historically named hosts.csv)."""
    path = p.Path(file_hosts_jsonl)
    if not path.is_file():
        raise RuntimeError(f"file does not exist: {path}")
    hosts: List[HostInfo] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                hosts.append(host_from_record(json.loads(line)))
            except (json.JSONDecodeError, ValueError) as exc:
                print(f"[{get_timestamp()}] skipping {path}:{line_number}: {exc}")
    return hosts

# Backward-compatible function name; the backing file is now JSON Lines.
def load_hosts_csv(file_hosts_csv: os.PathLike | str) -> List[HostInfo]:
    return load_hosts_jsonl(file_hosts_csv)

def preferred_inventory_ip(entry: InventoryEntry) -> str | None:
    """Keep the existing preference: standalone first, then dev."""
    return entry.get_stand_alone_ip() or entry.get_dev_ip() or None

def distro_group_name(distro: str, major_version: str) -> str:
    return f"{sanitize_group_name(distro)}{re.sub(r'[^0-9A-Za-z]+', '', str(major_version))}x"

def write_group_inventory(file_path: p.Path, group_name: str, host_to_ip: Dict[str, str]) -> None:
    """Write host sections followed by a parent :children section."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as stream:
        for hostname in sorted(host_to_ip):
            ip = host_to_ip[hostname]
            if not ip:
                continue
            stream.write(f"[{hostname}]\n{ip}\n\n")
        stream.write(f"[{group_name}:children]\n")
        for hostname in sorted(host_to_ip):
            if host_to_ip[hostname]:
                stream.write(f"{hostname}\n")

def write_subnets(file_inventory: os.PathLike | str, inventory: Inventory) -> None:
    sections = [
        ("unknown", inventory.get_unknown_ip_list()),
        ("management", inventory.get_management_ip_list()),
        ("nipr", inventory.get_nipr_ip_list()),
        ("dev", inventory.get_dev_ip_list()),
        ("standalone", inventory.get_stand_alone_ip_list()),
        ("old_nipr", inventory.get_old_nipr_ip_list()),
    ]
    with open(file_inventory, "w", encoding="utf-8") as stream:
        for section, addresses in sections:
            filtered = [ip for ip in addresses if ip and not ip.startswith(("0.", "127.", "169.254.", "172.17."))]
            if not filtered:
                continue
            stream.write(f"\n[{section}]\n")
            for ip in sorted(set(filtered)):
                stream.write(f"{ip}\n")

def glob_children(location: os.PathLike | str = "./") -> Set[str]:
    """Return every inventory group represented by a recursively found *.list file."""
    return {
        p.Path(path).stem
        for path in glob_files(str(location), "*.list", True)
        if p.Path(path).name != "world.list"
    }

def write_world_file(directory_inventory: os.PathLike | str) -> None:
    directory = p.Path(directory_inventory)
    world_file = directory / "world.list"
    children = sorted(glob_children(directory))
    with world_file.open("w", encoding="utf-8") as stream:
        stream.write("[world:children]\n")
        for child in children:
            stream.write(f"{child}\n")
        stream.write("\n")
        for child in children:
            stream.write(f"[{child}]\n")
    world_vars = directory / "world.vars"
    if world_vars.exists():
        write_file(world_file, "a", "\n")
        merge_files(world_vars, world_file)
        world_vars.unlink()

def write_inventory(list_hosts: Iterable[HostInfo], directory_inventory: os.PathLike | str = "./inventories") -> None:
    """Generate distro, local-role, subnet, and world inventories."""
    destination = p.Path(directory_inventory)
    if destination.exists():
        delete_directory(str(destination))
    clone_everything(GLOBAL_STATIC_COPY_DIRECTORY, str(destination))
    inventory = Inventory()
    distro_members: Dict[str, Dict[str, str]] = defaultdict(dict)
    localrole_members: Dict[str, Dict[str, str]] = defaultdict(dict)
    for host in list_hosts:
        entry = InventoryEntry()
        entry.add_host(host)
        inventory.add_entry(entry)
        ip = preferred_inventory_ip(entry)
        if not ip:
            debug(f"no standalone/dev IP for {entry.get_host_name()}; omitting it from generated host groups")
            continue
        distro_group = distro_group_name(entry.get_distro(), entry.get_release())
        if distro_group and entry.get_release():
            distro_members[distro_group][entry.get_host_name()] = ip
        for role_group in entry.get_localrole_groups():
            localrole_members[role_group][entry.get_host_name()] = ip
    # /ansible/inventory/redhat10x/redhat10x.list
    for group_name, members in sorted(distro_members.items()):
        write_group_inventory(destination / group_name / f"{group_name}.list", group_name, members)
    # /ansible/inventory/groups/prod.list, webservers.list, oracle.list, etc.
    groups_directory = destination / "groups"
    groups_directory.mkdir(parents=True, exist_ok=True)
    for group_name, members in sorted(localrole_members.items()):
        write_group_inventory(groups_directory / f"{group_name}.list", group_name, members)
    write_subnets(destination / "inventory", inventory)
    write_world_file(destination)
    debug(f"generated {len(distro_members)} distro inventories and {len(localrole_members)} local-role inventories")

def main() -> int:
    debug(f"parser version: {PARSER_VERSION}")
    debug(f"executing parser: {p.Path(__file__).resolve()}")
    debug(f"humangroup lookup module: {p.Path(__import__('libhumangroupinfo').__file__).resolve()}")
    try:
        hosts = load_hosts(GLOBAL_HOSTS_INFO_DIRECTORY)
        write_inventory(hosts, GLOBAL_INVENTORY_DIRECTORY)
    except (OSError, RuntimeError) as exc:
        print(f"[{get_timestamp()}] fatal: {exc}")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
