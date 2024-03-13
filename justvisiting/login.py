import paramiko
import configparser
import ipaddress
import os
import concurrent.futures
from libconnectionhost import * 

# Load Configuration from INI File
config = configparser.ConfigParser()
try:
    config.read('config.ini')
    # Assuming SSH key paths and valid IP ranges are defined in the config.ini
    GLOBAL_CONFIG = {
        "ssh_user_keys": {user: config['SSH_KEYS'][user] for user in config['SSH_KEYS']},
        "valid_ip_ranges": [
            "10.1.1.0/24",
            "192.168.131.0/24",
            "137.244.161.0/24",
            "137.244.170.0/24"
        ],
        "ansible_hosts_file": config['SSH']['ansible_hosts_file']
    }
except Exception as e:
    print(f"Failed to read or validate configuration file: {e}")
    exit(1)

def inventory_exists(inventory_path):
    return os.path.exists(inventory_path)

def ip_in_range(ip, ranges):
    for range in ranges:
        if ipaddress.ip_address(ip) in ipaddress.ip_network(range):
            return True
    return False

def parse_ansible_hosts(file_path):
    hosts = []
    try:
        with open(file_path, 'r') as file:
            skip_section = False
            for line in file:
                line = line.strip()
                if line.startswith("["):
                    skip_section = "unknown" in line.lower()
                    continue
                if skip_section or not line or line.startswith("#"):
                    continue
                if ip_in_range(line, GLOBAL_CONFIG["valid_ip_ranges"]):
                    hosts.append(Host(line))  # Assuming Host is defined in libconnectionhost
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    return hosts

def is_ip_valid(ip: str) -> bool:
    ip_obj = ipaddress.ip_address(ip)
    for cidr in GLOBAL_CONFIG["valid_ip_ranges"]:
        if ip_obj in ipaddress.ip_network(cidr, strict=False):
            return True
    return False

def ssh_into(ip: str, username: str, ssh_key_path: str) -> str:
    try:
        with paramiko.SSHClient() as ssh_client:
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(ip, username=username, key_filename=ssh_key_path)
        return f"Success: Connected to {ip} as {username}"
    except Exception as e:
        return f"Failed: Connecting to {ip} as {username}: {e}"

def attempt_ssh(ip: str) -> None:
    if not is_ip_valid(ip):
        print(f"The IP address {ip} is not within the allowed ranges.")
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=int(config['App']['workers'])) as executor:
        futures = []
        for username, ssh_key_path in GLOBAL_CONFIG["ssh_user_keys"].items():
            futures.append(executor.submit(ssh_into, ip, username, ssh_key_path))

        for future in concurrent.futures.as_completed(futures):
            print(future.result())

def main():
    hosts_info = parse_ansible_hosts(GLOBAL_CONFIG["ansible_hosts_file"])
    for host in hosts_info:
        attempt_ssh(host.ip)  # Assuming Host object has an 'ip' attribute


if __name__ == "__main__":
    main()
