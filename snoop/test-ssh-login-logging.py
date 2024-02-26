from dataclasses import dataclass, field
import paramiko
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor, as_completed
import configparser
import logging
import smtplib

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

@dataclass
class Host:
    hostname: str
    ip_address: str
    connection_state: str = "Not Attempted"

@dataclass
class EmailConfig:
    sender: str
    recipients: str
    smtp_server: str
    smtp_port: int
    smtp_user: str
    smtp_password: str

    def send_email(self, subject: str, body: str):
        recipients_list = self.recipients.split(',')  # Convert recipients string to list
        message = MIMEMultipart()
        message['From'] = self.sender
        message['To'] = ", ".join(recipients_list)
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.sender, recipients_list, message.as_string())
                logging.info("Email sent successfully.")
        except Exception as e:
            logging.error(f"Failed to send email: {e}")

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
        email_config.send_email("SSH Login Failure Report", body)

if __name__ == "__main__":
    main()