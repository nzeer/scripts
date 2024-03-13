import paramiko
from concurrent.futures import ThreadPoolExecutor, as_completed
import configparser
import colorlog
import logging
import os
from libconnectionhost import *
import ipaddress

# Load Configuration from INI File
config = configparser.ConfigParser()
try:
    config.read('config.ini')
    # Validate essential configuration exists
    essential_ssh_keys = ['ansible_hosts_file', 'ssh_user', 'ssh_key_path']
    if not all(key in config['SSH'] for key in essential_ssh_keys):
        raise ValueError("Missing essential SSH configuration.")
    log_file_path = config['Logging']['log_file']  # Load log file path
except Exception as e:
    print(f"Failed to read or validate configuration file: {e}")  # Use print because logging is not set up yet
    exit(1)

GLOBAL_CONFIG = {
    "ssh_user_info": {"rjackson": "12345abc", "jgrayjr": "123abc", "tmccombs": "abc123", "gsanders": "abc123"},
    "valid_ip_ranges": ["10.1.1.0/24", "192.168.131.0/24", "137.244.161.0/24", "137.244.170.0/24"],
}

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Set the log level to INFO

# Create console handler and set level to debug
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create a formatter with color
formatter = colorlog.ColoredFormatter(
    "%(blue)s[%(asctime)s] %(log_color)s%(levelname)-8s%(reset)s %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)

# Create file handler and set level to debug
file_handler = logging.FileHandler(log_file_path)  # Log messages to this file
file_handler.setLevel(logging.DEBUG)

# Create formatter and add it to the handlers
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Now you can use logging as before
logging.info("Initializing logging...")

def ip_in_range(ip, ranges):
    logging.debug(f"testing ip: {ip}")
    for range in ranges:
        logging.debug(f"testing range: {range}")
        if ipaddress.ip_address(ip) in ipaddress.ip_network(range):
            logging.debug(f"IP: {ip} is in range: {range}")
            return True
    logging.debug(f"IP: {ip} not found in range: {range}")
    return False

def parse_ansible_hosts2(file_path, ip_ranges):
    hosts_info = []
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for i in range(0, len(lines), 2):
                hostname = lines[i].strip().strip('[]')
                ip_address = lines[i + 1].strip()
                if ip_in_range(ip_address, ip_ranges):
                    hosts_info.append(Host(ip_address))
    except Exception as e:
        logging.error(f"Error parsing hosts file: {e}")
        exit(1)
    return hosts_info

def parse_ansible_hosts(file_path, *, valid_ranges=None):
    hosts = []
    valid_ranges = GLOBAL_CONFIG["valid_ip_ranges"]
    skip_section = False
    with open(file_path, 'r') as file:
        for line in file:
            logging.debug(f"Parsing line: {line}")
            line = line.strip()
            if line.startswith("["):
                # Check if the section is [unknown], if so, skip it
                skip_section = "unknown" in line.lower()
                continue
            if skip_section or not line or line.startswith("#"):
                continue
            if ip_in_range(line, valid_ranges):
                hosts.append(Host(line))
                logging.debug(f"Added host: {line}")
    return hosts

def inventory_exists(inventory_path):
    if not os.path.exists(inventory_path):
        return False
    return True

def test_ssh_login(host):
    try:
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host.ip_address, username=config['SSH']['ssh_user'], key_filename=config['SSH']['ssh_key_path'])
        host.connection_state = "Success"
    except Exception as e:
        host.connection_state = "Failed"
        logging.error(f"SSH connection failed for {host.hostname}: {e}")
    return host

def main():
    hosts_info = parse_ansible_hosts(config['SSH']['ansible_hosts_file'])

    with ThreadPoolExecutor(max_workers=int(config['App']['workers'])) as executor:
        futures = [executor.submit(test_ssh_login, host) for host in hosts_info]
        for future in as_completed(futures):
            future.result()  # This is to ensure any exceptions raised in threads are handled

    successful_logins = [host for host in hosts_info if host.connection_state == "Success"]
    unsuccessful_logins = [host for host in hosts_info if host.connection_state == "Failed"]

    logging.info(f"Total successful connections: {len(successful_logins)}")
    logging.info(f"Total unsuccessful connections: {len(unsuccessful_logins)}")

if __name__ == "__main__":
    main()