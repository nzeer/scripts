import pathlib as p
from dataclasses import dataclass

""" =========================================================
parse files in ./hosts and build inventories based off:
  - ip (configurable)
  - os family
  - major release version
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

    def os_version(self) -> str:
        return self.os_info_list[1]

    def os_family(self) -> str:
        return self.os_info_list[0]


# print (type(self.name))
# <class 'str'>
# Expected behavior <class datetime.datetime>
