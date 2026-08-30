import pathlib as p
from dataclasses import dataclass

""" =========================================================
Dataclass for holding ansible setup facts:
  - ip (configurable)
  - os family
  - major release version
  - fqdn
============================================================="""


@dataclass
class HostInfo:
    """Class for tracking host info"""

    name: str
    ip_list: list
    os_info_list: list

    def fqdn(self) -> str:
        return self.name

    def ips(self) -> list:
        return self.ip_list

    def version(self) -> str:
        return self.os_info_list[1]

    def distro(self) -> str:
        return self.os_info_list[0]


# print (type(self.name))
# <class 'str'>
# Expected behavior <class datetime.datetime>
