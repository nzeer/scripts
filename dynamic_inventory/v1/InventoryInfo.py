from dataclasses import dataclass

""" =========================================================
Dataclass for holding ansible inventory info:
  - ip (configurable)
  - os family
  - major release version
  - fqdn
============================================================="""


@dataclass
class InventoryInfo:
    """Class for tracking host info"""

    ip_nipr_dict
    ip_stand_alone_dict
    ip_dev_dict
    name: str

    def fqdn(self) -> str:
        return self.name

    def nipr(self) -> dict:
        return self.ip_nipr_dict

    def dev(self) -> dict:
        return self.ip_dev_dict

    def stand_alone(self) -> dict:
        return self.ip_stand_alone_dict
