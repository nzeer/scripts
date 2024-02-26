from dataclasses import dataclass
import paramiko
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor, as_completed
import configparser
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load Configuration from INI File
config = configparser.ConfigParser()
try:
    config.read('config.ini')
    # Validate essential configuration exists
    essential_keys = ['ansible_hosts_file', 'ssh_user', 'ssh_key_path']
    if not all(key in config['SSH'] for key in essential_keys):
        raise ValueError("Missing essential SSH configuration.")
except Exception as e:
    logging.error(f"Failed to read or validate configuration file: {e}")
    exit(1)

@dataclass
class Host:
    hostname: str
    ip_address: str
    connection_state: str = "Not Attempted"

def parse_ansible_hosts(file_path):
    hosts_info = []
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for i in range(0, len(lines), 2):
                hostname = lines[i].strip().strip('[]')
                ip_address = lines[i + 1].strip()
                hosts_info.append(Host(hostname, ip_address))
    except Exception as e:
        logging.error(f"Error parsing hosts file: {e}")
        exit(1)
    return hosts_info

def test_ssh_login(host):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host.ip_address, username=config['SSH']['ssh_user'], key_filename=config['SSH']['ssh_key_path'])
        ssh.close()
        host.connection_state = "Success"
    except Exception as e:
        host.connection_state = "Failed"
        logging.error(f"SSH connection failed for {host.hostname}: {e}")
    return host

def send_email(subject, body, sender, recipients):
    try:
        message = MIMEMultipart()
        message['From'] = sender
        message['To'] = ", ".join(recipients.split(','))
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP(config['Email']['smtp_server'], config['Email'].getint('smtp_port')) as server:
            server.starttls()
            server.login(config['Email']['smtp_user'], config['Email']['smtp_password'])
            server.sendmail(sender, recipients.split(','), message.as_string())
            logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def main():
    hosts_info = parse_ansible_hosts(config['SSH']['ansible_hosts_file'])

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(test_ssh_login, host) for host in hosts_info]
        for future in as_completed(futures):
            future.result()  # This is to ensure any exceptions raised in threads are handled

    successful_logins = [host for host in hosts_info if host.connection_state == "Success"]
    unsuccessful_logins = [host for host in hosts_info if host.connection_state == "Failed"]

    logging.info(f"Total successful connections: {len(successful_logins)}")
    logging.info(f"Total unsuccessful connections: {len(unsuccessful_logins)}")

    if unsuccessful_logins:
        body = "Unsuccessful SSH login attempts:\n" + "\n".join([f"{host.hostname} ({host.ip_address}) - {host.connection_state}" for host in unsuccessful_logins])
        send_email("SSH Login Failure Report", body, config['Email']['email_sender'], config['Email']['email_recipients'])

if __name__ == "__main__":
    main()