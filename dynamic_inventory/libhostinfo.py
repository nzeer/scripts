"""Host fact model used by the dynamic inventory generator."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class HostInfo:
    """Normalized facts for one host."""
    name: str = ""
    ip_list: List[str] = field(default_factory=list)
    os_info_list: List[str] = field(default_factory=list)
    os_distro: str = ""
    os_distro_version_major: str = ""
    ip_mac_addresses: List[Dict[str, str]] = field(default_factory=list)
    os_info: Dict[str, str] = field(default_factory=dict)
    os_distro_version_minor: str = ""
    os_distro_version_full: str = ""
    localroleinfo: str = ""
    localrole_groups: List[str] = field(default_factory=list)
    hostname: str = ""
    def __post_init__(self) -> None:
        # Support legacy callers that still provide list-based OS data.
        if not self.os_info and self.os_info_list:
            self.os_info = {
                "distribution": str(self.os_info_list[0]) if len(self.os_info_list) > 0 else "",
                "major_version": str(self.os_info_list[1]) if len(self.os_info_list) > 1 else "",
                "minor_version": str(self.os_info_list[2]) if len(self.os_info_list) > 2 else "",
                "full_version": str(self.os_info_list[3]) if len(self.os_info_list) > 3 else "",
            }
        if self.os_info:
            self.set_os_info(self.os_info)
        # Support either the new MAC/IP records or the legacy plain IP list.
        if self.ip_mac_addresses:
            self.set_ip_mac_addresses(self.ip_mac_addresses)
        elif self.ip_list:
            self.ip_list = self._dedupe_strings(self.ip_list)
        if not self.hostname and self.name:
            self.hostname = self.name.split(".", 1)[0]
    @staticmethod
    def _dedupe_strings(values: List[Any]) -> List[str]:
        seen = set()
        result: List[str] = []
        for value in values:
            text = str(value).strip()
            if text and text not in seen:
                seen.add(text)
                result.append(text)
        return result
    def get_os_info_list(self) -> List[str]:
        return self.os_info_list
    def set_os_info_list(self, os_info: List[Any]) -> None:
        self.os_info_list = [str(item) for item in os_info]
        self.set_os_info(self.os_info_list)
    def get_os_info(self) -> Dict[str, str]:
        return self.os_info
    def get_fqdn(self) -> str:
        return self.name
    def set_fqdn(self, name: str) -> None:
        self.name = name
    # Preserve the original misspelled method for old callers.
    def set_fqdb(self, name: str) -> None:
        self.set_fqdn(name)
    def get_hostname(self) -> str:
        return self.hostname or self.name.split(".", 1)[0]
    def get_ip_list(self) -> List[str]:
        return self.ip_list
    def set_ip_list(self, ip_list: List[Any]) -> None:
        self.ip_list = self._dedupe_strings(ip_list)
    def get_ip_mac_addresses(self) -> List[Dict[str, str]]:
        return self.ip_mac_addresses
    def set_ip_mac_addresses(self, records: List[Dict[str, Any]]) -> None:
        normalized: List[Dict[str, str]] = []
        seen = set()
        for record in records or []:
            if not isinstance(record, dict):
                continue
            mac = str(record.get("mac", "")).strip().lower()
            ip = str(record.get("ip", "")).strip()
            if not ip:
                continue
            key = (mac, ip)
            if key in seen:
                continue
            seen.add(key)
            normalized.append({"mac": mac, "ip": ip})
        self.ip_mac_addresses = normalized
        self.ip_list = self._dedupe_strings([item["ip"] for item in normalized])
    def get_version(self) -> str:
        return self.os_distro_version_major
    def set_version(self, version: Any) -> None:
        self.os_distro_version_major = str(version or "")
        self.os_info["major_version"] = self.os_distro_version_major
        self._sync_os_info_list()
    def get_minor_version(self) -> str:
        return self.os_distro_version_minor
    def get_full_version(self) -> str:
        return self.os_distro_version_full
    def get_distro(self) -> str:
        return self.os_distro
    def set_distro(self, distro: Any) -> None:
        self.os_distro = str(distro or "").lower()
        self.os_info["distribution"] = str(distro or "")
        self._sync_os_info_list()
    def set_os_info(self, os_info: Any = None) -> None:
        if isinstance(os_info, dict):
            self.os_info = {
                "distribution": str(os_info.get("distribution", "") or ""),
                "major_version": str(os_info.get("major_version", "") or ""),
                "minor_version": str(os_info.get("minor_version", "") or ""),
                "full_version": str(os_info.get("full_version", "") or ""),
            }
        elif isinstance(os_info, (list, tuple)):
            values = list(os_info)
            self.os_info = {
                "distribution": str(values[0]) if len(values) > 0 else "",
                "major_version": str(values[1]) if len(values) > 1 else "",
                "minor_version": str(values[2]) if len(values) > 2 else "",
                "full_version": str(values[3]) if len(values) > 3 else "",
            }
        else:
            self.os_info = {
                "distribution": "",
                "major_version": "",
                "minor_version": "",
                "full_version": "",
            }
        self.os_distro = self.os_info["distribution"].lower()
        self.os_distro_version_major = self.os_info["major_version"]
        self.os_distro_version_minor = self.os_info["minor_version"]
        self.os_distro_version_full = self.os_info["full_version"]
        self._sync_os_info_list()
    def _sync_os_info_list(self) -> None:
        self.os_info_list = [
            self.os_info.get("distribution", ""),
            self.os_info.get("major_version", ""),
            self.os_info.get("minor_version", ""),
            self.os_info.get("full_version", ""),
        ]
    def get_os_info_tuple(self) -> tuple:
        return tuple(self.os_info_list)
    def get_localroleinfo(self) -> str:
        return self.localroleinfo
    def get_localrole_groups(self) -> List[str]:
        return self.localrole_groups
    def add_ip(self, ip: str, mac: str = "") -> None:
        ip = str(ip).strip()
        if not ip:
            return
        if ip not in self.ip_list:
            self.ip_list.append(ip)
        record = {"mac": str(mac).strip().lower(), "ip": ip}
        if record not in self.ip_mac_addresses:
            self.ip_mac_addresses.append(record)
