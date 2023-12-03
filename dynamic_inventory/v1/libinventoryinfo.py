from dataclasses import dataclass
from typing import List

from typing_extensions import Iterator

from libhostinfo import HostInfo

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

    nipr_ip: str
    dev_ip: str
    stand_alone_ip: str
    unknown_subnet_ip: str
    hostname: str
    ip_list: list
    distro: str
    release: str

    def get_distro(self) -> str:
        return self.distro

    def set_distro(self, d):
        self.distro = d

    def get_release(self) -> str:
        return self.release

    def set_release(self, r):
        self.release = r

    def get_nipr_ip(self) -> str:
        return self.nipr_ip

    def get_dev_ip(self) -> str:
        return self.dev_ip

    def get_stand_alone_ip(self) -> str:
        return self.stand_alone_ip

    def get_unknown_ip(self) -> str:
        return self.unknown_subnet_ip

    def get_host_name(self) -> str:
        return self.hostname

    def get_ip_list(self) -> list:
        return self.ip_list

    # def add_host(self, host=HostInfo(name="", ip_list==[], os_info_list=[])):
    def add_host(self, host):
        self.hostname = host.get_fqdn()
        for h in host.get_ip_list():
            self.get_ip_list().append(h)
        self.release = host.get_version()
        self.distro = host.get_distro()


@dataclass
class Inventory:
    items: List[InventoryEntry]
    list_nipr: list
    list_dev: list
    list_stand_alone: list
    list_unknown: list
    # list_inventory_entries: list

    def get_inventory_entries(self) -> List[InventoryEntry]:
        return self.items

    def get_nipr_ip_list(self) -> list:
        return self.list_nipr

    def set_nipr_ip_list(self, ip_list=[]):
        self.list_nipr = ip_list

    def get_dev_ip_list(self) -> list:
        return self.list_dev

    def set_dev_ip_list(self, ip_list=[]):
        self.list_dev = ip_list

    def get_stand_alone_ip_list(self) -> list:
        return self.list_stand_alone

    def set_stand_alone_ip_list(self, ip_list=[]):
        self.list_stand_alone = ip_list

    def get_unknown_ip_list(self) -> list:
        return self.list_unknown

    def set_unknown_ip_list(self, ip_list=[]):
        self.list_unknown = ip_list

    def add_nipr(self, ip=""):
        self.get_nipr_ip_list().append(ip)

    def add_dev(self, ip=""):
        self.get_dev_ip_list().append(ip)

    def add_stand_alone(self, ip=""):
        self.get_stand_alone_ip_list().append(ip)

    def add_unknown(self, ip=""):
        self.get_unknown_ip_list().append(ip)

    def add_entry(self, invEntry):
        self.get_inventory_entries().append(invEntry)
        self.add_ip(invEntry.get_ip_list())

    def add_ip(self, ip_list=[]):
        # check which network, and add to the appropriate list
        try:
            if not type(ip_list) is list:
                l = [ip_list]
            else:
                l = ip_list
            iterator = iter(l)
            while True:
                ip = next(iterator)
                self.find_subnet(ip).append(ip)
        except StopIteration:
            pass

    def find_subnet(self, ip) -> list:
        if ip.find("192.168."):
            return self.get_dev_ip_list()
        elif ip.find("10.0."):
            return self.get_stand_alone_ip_list()
        elif ip.find("131."):
            return self.get_nipr_ip_list()
        else:
            print("unknown")
            return self.get_unknown_ip_list()
