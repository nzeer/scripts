"""Inventory models and subnet classification helpers."""
from __future__ import annotations
from dataclasses import dataclass, field
from ipaddress import ip_address
from typing import Dict, List
from libhostinfo import HostInfo

@dataclass
class InventoryEntry:
    nipr_ip: str = ""
    management_ip: str = ""
    dev_ip: str = ""
    stand_alone_ip: str = ""
    unknown_subnet_ip: str = ""
    old_nipr_ip: str = ""
    hostname: str = ""
    ip_list: List[str] = field(default_factory=list)
    distro: str = ""
    release: str = ""
    ip_mac_addresses: List[Dict[str, str]] = field(default_factory=list)
    os_info: Dict[str, str] = field(default_factory=dict)
    localroleinfo: str = ""
    localrole_groups: List[str] = field(default_factory=list)
    def get_distro(self) -> str:
        return self.distro
    def set_distro(self, distro: str) -> None:
        self.distro = str(distro or "").lower()
    def get_release(self) -> str:
        return self.release
    def set_release(self, release: str) -> None:
        self.release = str(release or "")
    def get_nipr_ip(self) -> str:
        return self.nipr_ip
    def get_dev_ip(self) -> str:
        return self.dev_ip
    def set_dev_ip(self, ip: str) -> None:
        self.dev_ip = ip
    def get_old_nipr_ip(self) -> str:
        return self.old_nipr_ip
    def set_old_nipr_ip(self, ip: str) -> None:
        self.old_nipr_ip = ip
    def set_nipr_ip(self, ip: str) -> None:
        self.nipr_ip = ip
    def set_unknown_ip(self, ip: str) -> None:
        self.unknown_subnet_ip = ip
    def set_management_ip(self, ip: str) -> None:
        self.management_ip = ip
    def set_stand_alone_ip(self, ip: str) -> None:
        self.stand_alone_ip = ip
    def get_stand_alone_ip(self) -> str:
        return self.stand_alone_ip
    def get_unknown_ip(self) -> str:
        return self.unknown_subnet_ip
    def get_management_ip(self) -> str:
        return self.management_ip
    def get_host_name(self) -> str:
        return self.hostname
    def set_host_name(self, hostname: str) -> None:
        self.hostname = hostname
    def get_ip_list(self) -> List[str]:
        return self.ip_list
    def get_ip_mac_addresses(self) -> List[Dict[str, str]]:
        return self.ip_mac_addresses
    def get_os_info(self) -> Dict[str, str]:
        return self.os_info
    def get_localroleinfo(self) -> str:
        return self.localroleinfo
    def get_localrole_groups(self) -> List[str]:
        return self.localrole_groups
    def add_host(self, host: HostInfo) -> None:
        self.set_host_name(host.get_hostname())
        self.ip_list = list(host.get_ip_list())
        self.ip_mac_addresses = list(host.get_ip_mac_addresses())
        for ip in self.ip_list:
            self.record_subnet(ip)
        self.set_release(host.get_version())
        self.set_distro(host.get_distro())
        self.os_info = dict(host.get_os_info())
        self.localroleinfo = host.get_localroleinfo()
        self.localrole_groups = list(host.get_localrole_groups())
    def record_subnet(self, ip: str) -> None:
        try:
            address = ip_address(ip)
        except ValueError:
            return
        if address.version != 4:
            return
        octets = ip.split(".")
        if octets[:3] == ["192", "168", "131"]:
            self.set_dev_ip(ip)
        elif octets[:3] == ["10", "1", "1"]:
            self.set_stand_alone_ip(ip)
        elif octets[:2] == ["10", "9"]:
            self.set_management_ip(ip)
        elif octets[0] == "131":
            self.set_nipr_ip(ip)
        elif octets[0] == "137":
            self.set_old_nipr_ip(ip)
        elif octets[:2] != ["172", "17"] and octets[0] not in {"127", "0", "169"}:
            self.set_unknown_ip(ip)

@dataclass
class Inventory:
    items: List[InventoryEntry] = field(default_factory=list)
    list_nipr: List[str] = field(default_factory=list)
    list_management: List[str] = field(default_factory=list)
    list_dev: List[str] = field(default_factory=list)
    list_stand_alone: List[str] = field(default_factory=list)
    list_old_nipr: List[str] = field(default_factory=list)
    list_unknown: List[str] = field(default_factory=list)
    list_formatted_host_entries: List[dict] = field(default_factory=list)
    dict_unknown_subnet: dict = field(default_factory=dict)
    def print_ips(self) -> None:
        print("dev: ", self.list_dev)
        print("nipr: ", self.list_nipr)
        print("unknown: ", self.list_unknown)
        print("management: ", self.list_management)
        print("standalone: ", self.list_stand_alone)
        print("old nipr: ", self.list_old_nipr)
        print("formatted hosts: ", self.list_formatted_host_entries)
    def get_dict_unknown_subnet(self) -> dict:
        return self.dict_unknown_subnet
    def get_list_formatted_host_entries(self) -> List[dict]:
        return self.list_formatted_host_entries
    def get_inventory_entries(self) -> List[InventoryEntry]:
        return self.items
    def get_nipr_ip_list(self) -> List[str]:
        return self.list_nipr
    def get_dev_ip_list(self) -> List[str]:
        return self.list_dev
    def get_stand_alone_ip_list(self) -> List[str]:
        return self.list_stand_alone
    def get_old_nipr_ip_list(self) -> List[str]:
        return self.list_old_nipr
    def get_unknown_ip_list(self) -> List[str]:
        return self.list_unknown
    def get_management_ip_list(self) -> List[str]:
        return self.list_management
    def add_entry(self, entry: InventoryEntry) -> None:
        self.items.append(entry)
        self.add_ip(entry.get_ip_list())
    def add_ip(self, ip_list) -> None:
        values = ip_list if isinstance(ip_list, list) else [ip_list]
        for ip in values:
            target = self.find_subnet(ip)
            if ip and ip not in target:
                target.append(ip)
    def find_subnet(self, ip: str) -> List[str]:
        try:
            address = ip_address(ip)
        except ValueError:
            return self.list_unknown
        if address.version != 4:
            return self.list_unknown
        octets = ip.split(".")
        if octets[:3] == ["192", "168", "131"]:
            return self.list_dev
        if octets[:3] == ["10", "1", "1"]:
            return self.list_stand_alone
        if octets[:2] == ["10", "9"]:
            return self.list_management
        if octets[0] == "137":
            return self.list_old_nipr
        if octets[0] == "131":
            return self.list_nipr
        return self.list_unknown
