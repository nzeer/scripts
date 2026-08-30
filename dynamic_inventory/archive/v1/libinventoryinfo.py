from dataclasses import dataclass
from typing import List

from libhostinfo import HostInfo
from typing_extensions import Iterator

debug = False

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
    """Class for tracking inventory entry info"""

    nipr_ip: str
    dev_ip: str
    stand_alone_ip: str
    unknown_subnet_ip: str
    old_stand_alone_ip: str
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

    def set_dev_ip(self, ip):
        self.dev_ip = ip

    def get_old_stand_alone_ip(self) -> str:
        return self.old_stand_alone_ip

    def set_old_stand_alone_ip(self, ip):
        self.old_stand_alone_ip = ip

    def set_nipr_ip(self, ip):
        self.nipr_ip = ip

    def set_unknown_ip(self, ip):
        self.unknown_subnet_ip = ip

    def set_stand_alone_ip(self, ip):
        self.stand_alone_ip = ip

    def get_stand_alone_ip(self) -> str:
        return self.stand_alone_ip

    def get_unknown_ip(self) -> str:
        return self.unknown_subnet_ip

    def get_host_name(self) -> str:
        return self.hostname

    def set_host_name(self, hn):
        self.hostname = hn

    def get_ip_list(self) -> list:
        return self.ip_list

    # def add_host(self, host=HostInfo(name="", ip_list==[], os_info_list=[])):
    def add_host(self, host):
        self.set_host_name(host.get_fqdn())
        for h in host.get_ip_list():
            self.get_ip_list().append(h)
            self.record_subnet(h)
        self.set_release(host.get_version())
        self.set_distro(host.get_distro())

    def record_subnet(self, ip):
        if debug:
            print("parsing: ", self.get_host_name())
        if debug:
            print("inv_entry_ip_switch", ip)
        octets = ip.split(".")
        if debug:
            print("switching on ", octets[0])
        if octets[0] == "192":
            self.set_dev_ip(ip)
        elif octets[0] == "10":
            self.set_stand_alone_ip(ip)
        elif octets[0] == "131":
            self.set_nipr_ip(ip)
        elif octets[0] == "137":
            self.set_old_stand_alone_ip(ip)
        else:
            self.set_unknown_ip(ip)
            if debug:
                print("found unknown inside inv_entry: ", self.get_unknown_ip())


@dataclass
class Inventory:
    """Class for tracking inventory info"""

    items: List[InventoryEntry]
    list_nipr: list
    list_dev: list
    list_stand_alone: list
    list_old_stand_alone: list
    list_unknown: list
    list_formatted_host_entries: List[dict]
    dict_unknown_subnet: dict

    def print_ips(self):
        print("dev: ", self.get_dev_ip_list())
        print("nipr: ", self.get_nipr_ip_list())
        print("unknown: ", self.get_unknown_ip_list())
        print("standalone: ", self.get_stand_alone_ip_list())
        print("old standalone: ", self.get_old_stand_alone_ip_list())
        print("formatted hosts: ", self.get_list_formatted_host_entries())

    def get_dict_unknown_subnet(self) -> dict:
        return self.dict_unknown_subnet

    def get_list_formatted_host_entries(self) -> List[dict]:
        return self.list_formatted_host_entries

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

    def get_old_stand_alone_ip_list(self) -> list:
        return self.list_old_stand_alone

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

    def add_old_stand_alone(self, ip=""):
        self.get_old_stand_alone_ip_list().append(ip)

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
        octets = ip.split(".")
        if octets[0] == "192":
            return self.get_dev_ip_list()
        elif octets[0] == "10":
            return self.get_stand_alone_ip_list()
        elif octets[0] == "137":
            return self.get_old_stand_alone_ip_list()
        elif octets[0] == "131":
            return self.get_nipr_ip_list()
        else:
            return self.get_unknown_ip_list()

