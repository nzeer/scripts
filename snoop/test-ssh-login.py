import paramiko
from concurrent.futures import ThreadPoolExecutor, as_completed
import configparser
import logging
import os
from libmail import *
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

# Initialize logging
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filemode='w')

def ip_in_range(ip, ranges):
    logging.debug(f"testing ip: {ip}")
    for range in ranges:
        logging.debug(f"testing range: {range}")
        if ipaddress.ip_address(ip) in ipaddress.ip_network(range):
            logging.debug(f"IP: {ip} is in range: {range}")
            return True
    logging.debug(f"IP: {ip} not found in range: {range}")
    return False

def parse_ansible_hosts(file_path, ip_ranges):
    hosts_info = []
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for i in range(0, len(lines), 2):
                hostname = lines[i].strip().strip('[]')
                ip_address = lines[i + 1].strip()
                if ip_in_range(ip_address, ip_ranges):
                    hosts_info.append(Host(hostname, ip_address))
    except Exception as e:
        logging.error(f"Error parsing hosts file: {e}")
        exit(1)
    return hosts_info

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

# Initialize EmailConfig with values from the configuration file
email_config = EmailConfig(
    sender=config['Email']['email_sender'],
    recipients=config['Email']['email_recipients'],
    smtp_server=config['Email']['smtp_server'],
    smtp_port=config['Email'].getint('smtp_port'),
    smtp_user=config['Email']['smtp_user'],
    smtp_password=config['Email']['smtp_password']
)

def main():
    hosts_info = parse_ansible_hosts(config['SSH']['ansible_hosts_file'], config['SSH']['ip_ranges'].split(','))

    with ThreadPoolExecutor(max_workers=int(config['App']['workers'])) as executor:
        futures = [executor.submit(test_ssh_login, host) for host in hosts_info]
        for future in as_completed(futures):
            future.result()  # This is to ensure any exceptions raised in threads are handled

    successful_logins = [host for host in hosts_info if host.connection_state == "Success"]
    unsuccessful_logins = [host for host in hosts_info if host.connection_state == "Failed"]

    logging.info(f"Total successful connections: {len(successful_logins)}")
    logging.info(f"Total unsuccessful connections: {len(unsuccessful_logins)}")

    if unsuccessful_logins:
        body = "Unsuccessful SSH login attempts:\n" + "\n".join([f"{host.hostname} ({host.ip_address}) - {host.connection_state}" for host in unsuccessful_logins])
        email_config.send_email("SSH Login Failure Report", body)

if __name__ == "__main__":
    main()