from dataclasses import dataclass
from typing import List

from HostInfo import HostInfo

""" =========================================================
Dataclass for holding ansible inventory info:
  - list of all nipr ips
  - list of all dev ips
  - list of all stand alone ips
  - dictionary of stand alone ips/hostnames
  - dictionary of dev ips/hostnames
  - dictionary of nipr ips/hostnames
============================================================="""


@dataclass
class InventoryEntry:
    """Class for tracking host info"""

    """ip_nipr_dict: dict
    ip_stand_alone_dict: dict
    ip_dev_dict: dict"""
    nipr_ip_list: list
    dev_ip_list: list
    stand_alone_ip_list: list
    unknown_subnet_ip_list: list
    hostname: str
    os_distro: str
    os_release: str
    ip_list: list

    """def nipr(self) -> dict:
        return self.ip_nipr_dict

    def dev(self) -> dict:
        return self.ip_dev_dict

    def stand_alone(self) -> dict:
        return self.ip_stand_alone_dict"""

    def nipr_ips(self) -> list:
        return self.nipr_ip_list

    def dev_ips(self) -> list:
        return self.dev_ip_list

    def stand_alone_ips(self) -> list:
        return self.stand_alone_ip_list

    def unknown_ips(self) -> list:
        return self.unknown_subnet_ip_list

    def host_name(self) -> str:
        return self.hostname

    def release(self) -> str:
        return self.os_release

    def distro(self) -> str:
        return self.os_distro

    def ip_list(self) -> list:
        return self.ip_list

    # def add_host(self, host=HostInfo(name="", ip_list==[], os_info_list=[])):
    def add_host(self, host):
        self.hostname = host.name
        self.os_distro = host.os_info_list[0]
        if len(host.os_info_list) > 1:
            self.os_release = host.os_info_list[1]
        self.ip_list = host.ip_list


@dataclass
class Inventory:
    items: List[InventoryEntry]
    list_nipr: list
    list_dev: list
    list_stand_alone: list
    list_unknown: list
    list_entries: list

    def inventory_entries(self) -> list:
        return self.list_entries

    def nipr_entries(self) -> list:
        return self.list_nipr

    def dev_entries(self) -> list:
        return self.list_dev

    def stand_alone_entries(self) -> list:
        return self.list_stand_alone

    def unknown_entries(self) -> list:
        return self.list_unknown

    def add_nipr(self, ip):
        self.list_nipr.append(ip)

    def add_dev(self, ip):
        self.list_dev.append(ip)

    def add_stand_alone(self, ip):
        self.list_stand_alone.append(ip)

    def add_unknown(self, ip):
        self.list_unknown.append(ip)

    def add_entry(self, invEntry):
        self.list_entries.append(invEntry)

        self.add_ip(invEntry.get_ip_list)

    def add_ip(self, ip_list=[]):
        # check which network, and add to the appropriate list
        for ip in ip_list:
            if "192" in ip:
                self.add_dev(ip)
            elif "10.0." in ip:
                self.add_stand_alone(ip)
            elif "131." in ip:
                self.add_nipr(ip)
            else:
                self.add_unknown(ip)
