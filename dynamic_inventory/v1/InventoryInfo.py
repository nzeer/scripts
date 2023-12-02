from dataclasses import dataclass
from typing import List

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

    ip_nipr_dict: dict
    ip_stand_alone_dict: dict
    ip_dev_dict: dict
    nipr_ip_list: list
    dev_ip_list: list
    stand_alone_ip_list: list
    hostname: str

    def nipr(self) -> dict:
        return self.ip_nipr_dict

    def dev(self) -> dict:
        return self.ip_dev_dict

    def stand_alone(self) -> dict:
        return self.ip_stand_alone_dict

    def nipr_ips(self) -> list:
        return self.nipr_ip_list

    def dev_ips(self) -> list:
        return self.dev_ip_list

    def stand_alone_ips(self) -> list:
        return self.stand_alone_ip_list

    def host_name(self) -> str:
        return self.hostname


@dataclass
class Inventory:
    items: List[InventoryEntry]
