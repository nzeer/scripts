"""Models and lookup rules for parsing /etc/humangroups values."""
from __future__ import annotations
from dataclasses import dataclass, field
import re
from typing import Dict, List, Set, Tuple
HUMANGROUP_LOOKUP_VERSION = "2026-07-10-humangroup-dataclass-v6"

@dataclass
class ParsedHumanGroup:
    """Normalized group information extracted from one humangroups value."""
    raw_value: str
    main_group: str = ""
    environment: str = ""
    special_groups: List[str] = field(default_factory=list)
    unmatched_lines: List[str] = field(default_factory=list)
    def all_groups(self) -> List[str]:
        return sorted(
            group
            for group in {
                self.main_group,
                self.environment,
                *self.special_groups,
            }
            if group
        )

@dataclass
class HumanGroupLookup:
    """Lookup tables and normalization rules for /etc/humangroups."""
    allow_unknown_main_groups: bool = True
    allow_unknown_environments: bool = True
    allow_unknown_special_groups: bool = True
    main_groups: Dict[str, str] = field(
        default_factory=lambda: {
            "OSVERSION": "osversion",
            "HOSTNAME": "hostname",
            "IPV4": "ipv4",
            "NIPR": "nipr",
            "NIPR-MAC": "nipr_mac",
            "NIPRMAC": "nipr_mac",
            "APACHE": "apache",
            "TOMCAT": "tomcat",
            "WORKSTATION": "workstation",
            "YUMREPO": "yumrepo",
            "STIGIMAGE": "stigimage",
            "TEAMCENTER": "teamcenter",
            "JBOSS": "jboss",
            "DOCKER": "docker",
            "DOCKERREGISTRY": "dockerregistry",
            "ATLASSIAN": "atlassian",
            "GITOPS": "gitops",
            "GITLAB": "gitlab",
            "DATABASE": "database",
            "ACAS": "acas",
            "DEPLOYMENTCENTER": "deploymentcenter",
            "NAGIOS": "nagios",
            "OPSUTILS": "opsutils",
            "GWSOLR": "gwsolr",
            "GWZK": "gwzk",
            "PACSOLR": "pacsolr",
        }
    )
    environments: Dict[str, str] = field(
        default_factory=lambda: {
            "OPS": "ops",
            "PROD": "prod",
            "TEST": "test",
            "BETA": "beta",
            "ALPHA": "alpha",
            "DEV": "dev",
            "IMAGE": "image",
        }
    )
    token_aliases: Dict[str, str] = field(
        default_factory=lambda: {
            "HTTPD": "webservers",
            "APACHE": "webservers",
            "NGINX": "webservers",
            "WEBSERVER": "webservers",
            "WEBSERVERS": "webservers",
            "ORACLE": "oracle",
            "MYSQL": "mysql",
            "MARIADB": "mariadb",
            "POSTGRES": "postgres",
            "POSTGRESQL": "postgres",
            "TOMCAT": "tomcats",
            "TOMCATS": "tomcats",
        }
    )
    # Multi-word product names are resolved before individual-token parsing.
    phrase_aliases: Dict[str, Tuple[str, ...]] = field(
        default_factory=lambda: {
            "NAGIOS XI": ("nagios",),
            # Preserve the currently accepted legacy behavior for this phrase.
            "DOCKER REGISTRY": ("docker", "registry"),
            "GIT OPS": ("git",),
        }
    )
    numbered_role_bases: Dict[str, str] = field(
        default_factory=lambda: {
            "PROD": "prod",
            "TOAPDB": "toapdb",
        }
    )
    ignored_tokens: Set[str] = field(
        default_factory=lambda: {
            "RH",
            "RHEL",
            "REDHAT",
            "LINUX",
            "OL",
            "ORACLELINUX",
            "CENTOS",
            "ROCKY",
            "ALMA",
            "XI",
        }
    )
    line_pattern: re.Pattern[str] = field(
        default_factory=lambda: re.compile(
            r"^\s*(?P<main>[A-Za-z][A-Za-z0-9_-]*)"
            r"\[(?P<environment>[^\]]+)\]"
            r"(?:-(?P<special>.*?))?"
            r"(?:\s+\([^)]*\))?\s*$",
            re.IGNORECASE,
        ),
        repr=False,
    )
    legacy_os_pattern: re.Pattern[str] = field(
        default_factory=lambda: re.compile(
            r"^(?:RH|RHEL|REDHAT|OL|ORACLELINUX|CENTOS|ROCKY|ALMA)\d+(?:\.\d+)?$",
            re.IGNORECASE,
        ),
        repr=False,
    )
    version_pattern: re.Pattern[str] = field(
        default_factory=lambda: re.compile(
            r"^(?:\d+(?:[._-]\d+)*[a-z]?|v\d+(?:[._-]\d+)*)$",
            re.IGNORECASE,
        ),
        repr=False,
    )
    @staticmethod
    def sanitize_group_name(value: str) -> str:
        result = str(value or "").strip().lower()
        result = re.sub(r"[^a-z0-9_]+", "_", result)
        result = re.sub(r"_+", "_", result).strip("_")
        if result and result[0].isdigit():
            result = f"group_{result}"
        return result
    def lookup_main_group(self, value: str) -> str:
        normalized = str(value or "").strip().upper()
        mapped = self.main_groups.get(normalized)
        if mapped:
            return mapped
        if self.allow_unknown_main_groups:
            return self.sanitize_group_name(value)
        return ""
    def lookup_environment(self, value: str) -> str:
        normalized = str(value or "").strip().upper()
        mapped = self.environments.get(normalized)
        if mapped:
            return mapped
        if self.allow_unknown_environments:
            return self.sanitize_group_name(value)
        return ""
    def normalize_token(self, value: str) -> str:
        normalized = str(value or "").strip().upper()
        if not normalized or normalized in self.ignored_tokens:
            return ""
        if self.version_pattern.fullmatch(normalized):
            return ""
        for base, group in self.numbered_role_bases.items():
            if re.fullmatch(rf"{re.escape(base)}\d+", normalized):
                return group
        mapped = self.token_aliases.get(normalized)
        if mapped:
            return mapped
        if self.allow_unknown_special_groups:
            return self.sanitize_group_name(value)
        return ""
    def parse_special_groups(self, special_text: str) -> List[str]:
        groups: Set[str] = set()
        # Commas, slashes, semicolons, plus signs, and pipes separate clauses.
        for clause in re.split(r"\s*[,;/+|]\s*", str(special_text or "")):
            clause = clause.strip(" -\t")
            if not clause:
                continue
            clause_upper = re.sub(r"\s+", " ", clause.upper()).strip()
            # Resolve known product phrases before processing remaining words.
            for phrase, mapped_groups in self.phrase_aliases.items():
                phrase_pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
                if phrase_pattern.search(clause_upper):
                    groups.update(mapped_groups)
                    clause_upper = phrase_pattern.sub(" ", clause_upper)
            for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]*|\d+[A-Za-z]?", clause_upper):
                group = self.normalize_token(token)
                if group:
                    groups.add(group)
        return sorted(groups)
    def parse(self, raw_value: str) -> ParsedHumanGroup:
        parsed = ParsedHumanGroup(raw_value=str(raw_value or ""))
        all_special_groups: Set[str] = set()
        main_groups: Set[str] = set()
        environments: Set[str] = set()
        for raw_line in parsed.raw_value.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            match = self.line_pattern.fullmatch(line)
            if not match:
                parsed.unmatched_lines.append(line)
                continue
            main_value = match.group("main")
            environment_value = match.group("environment")
            special_text = match.group("special") or ""
            # Existing deployed values use RH8/RH9/RH10 as a schema prefix.
            # Future values can use the authoritative main-group identifier here.
            if not self.legacy_os_pattern.fullmatch(main_value):
                main_group = self.lookup_main_group(main_value)
                if main_group:
                    main_groups.add(main_group)
            environment = self.lookup_environment(environment_value)
            if environment:
                environments.add(environment)
            all_special_groups.update(self.parse_special_groups(special_text))
        # The current file format normally carries one main group/environment.
        parsed.main_group = sorted(main_groups)[0] if main_groups else ""
        parsed.environment = sorted(environments)[0] if environments else ""
        parsed.special_groups = sorted(
            (main_groups | environments | all_special_groups)
            - {parsed.main_group, parsed.environment, ""}
        )
        return parsed
