import pathlib as p
from dataclasses import dataclass
from typing import List

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
    os_distro: str
    os_distro_version_major: str

    def get_os_info_list(self) -> list:
        return self.os_info_list

    def set_os_info_list(self, os_info):
        self.os_info_list = os_info

    def get_fqdn(self) -> str:
        return self.name

    def set_fqdb(self, name):
        self.name = name

    def get_ip_list(self) -> list:
        return self.ip_list

    def set_ip_list(self, ip_list):
        self.ip_list = ip_list

    def get_version(self) -> str:
        return self.os_distro_version_major

    def set_version(self, version):
        self.os_info_list[1] = version
        self.os_distro_version_major = version

    def get_distro(self) -> str:
        return self.os_distro

    def set_distro(self, distro):
        self.os_info_list[0] = distro
        self.os_distro = distro

    def set_os_info(self, os_info=[]):
        # verify we have at least, an os family
        if len(os_info) > 0:
            # set os info list
            self.set_os_info_list(os_info)
            # set the distro
            distro = self.get_os_info_list()[0]
            self.set_distro(distro)
            # set the version, if present
            if len(self.get_os_info_list()) > 1:
                version = self.get_os_info_list()[1]
                self.set_version(version)

    def get_os_info_tuple(self) -> tuple:
        return tuple(self.get_os_info_list(), self.get_distro(), self.get_version())

    def add_ip(self, ip):
        self.get_ip_list().append(ip)


# print (type(self.name))
# <class 'str'>
# Expected behavior <class datetime.datetime>
