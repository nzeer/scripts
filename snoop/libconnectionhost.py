from dataclasses import dataclass

@dataclass
class Host:
    hostname: str
    ip_address: str
    connection_state: str = "Not Attempted"