import paramiko
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ipaddress
import os
import shutil

DEBUG: bool = True

# Configuration
GLOBAL_TEST_LOGIN_CONFIG = {
    'valid_ranges': ["10.1.1.0/24", "192.168.131.0/24", "137.244.161.0/24", "137.244.170.0/24"],
    'ansible_hosts_file': "/inventory/inventory",
    'ssh_user': "rjackson",
    'ssh_key_path': "./id_rsa",
    'email_sender': "your_email@example.com",
    'email_recipients': ["recipient1@example.com", "recipient2@example.com"],
    'smtp_server': "smtp.example.com",
    'smtp_port': 587,  # or 465 for SSL
    'smtp_user': "smtp_user",
    'smtp_password': "smtp_password",
}

def inventory_exists(inventory_path):
    if not os.path.exists(inventory_path):
        return False
    return True

def ip_in_range(ip, ranges):
    if DEBUG:
        print("testing ip: ",ip)
    for range in ranges:
        if DEBUG:
            print("testing range: ",range)
        if ipaddress.ip_address(ip) in ipaddress.ip_network(range):
            if DEBUG:
                print(ip + " is in range " + range)
            return True
    return False

def parse_ansible_hosts(file_path, valid_ranges):
    hosts = []
    #valid_ranges = ["10.1.1.0/24", "192.168.131.0/24", "137.244.161.0/24", "137.244.170.0/24"]
    skip_section = False
    with open(file_path, 'r') as file:
        for line in file:
            if DEBUG:
                print(line)
            line = line.strip()
            if line.startswith("["):
                # Check if the section is [unknown], if so, skip it
                skip_section = "unknown" in line.lower()
                continue
            if skip_section or not line or line.startswith("#"):
                continue
            if ip_in_range(line, valid_ranges):
                hosts.append(line)
    return hosts

def key_based_connect(host, user, key_path) -> bool:
    pkey = paramiko.RSAKey.from_private_key_file(key_path)
    client = paramiko.SSHClient()
    policy = paramiko.AutoAddPolicy()
    client.set_missing_host_key_policy(policy)
    if DEBUG:
        print("trying: %s@%s using %s" % (user, host, key_path))
    try:
        client.connect(host, username=user, pkey=pkey)
        if DEBUG:
            print("successful connection to ", host)
        return True
    except Exception as e:
        if DEBUG:
            print(e)
        return False
    finally:
        client.close()

def test_ssh_login(host, username, key_path):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if DEBUG:
        print("trying: %s@%s using %s" % (username, host, key_path))
    try:
        ssh.connect(host, username=username, key_filename=key_path)
        ssh.close()
        if DEBUG:
            print("successful connection to ", host)
        return True
    except Exception as e:
        if DEBUG:
            print(e)
        return False

def send_email(subject, body, sender, recipients, smtp_server, smtp_port, smtp_user, smtp_password):
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = ", ".join(recipients)
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.sendmail(sender, recipients, message.as_string())
            if DEBUG:
                print("Email sent successfully!")
    except Exception as e:
        if DEBUG:
            print(f"Failed to send email: {e}")

def main():
    if not inventory_exists(GLOBAL_TEST_LOGIN_CONFIG["ansible_hosts_file"]):
            if DEBUG:
                print("failed to load inventory from ", GLOBAL_TEST_LOGIN_CONFIG["ansible_hosts_file"])
            exit(1)

    hosts = parse_ansible_hosts(GLOBAL_TEST_LOGIN_CONFIG["ansible_hosts_file"], GLOBAL_TEST_LOGIN_CONFIG['valid_ranges'])
    unsuccessful_logins = {}

    for host in hosts:
        if not key_based_connect(host, GLOBAL_TEST_LOGIN_CONFIG["ssh_user"], GLOBAL_TEST_LOGIN_CONFIG["ssh_key_path"]):
            unsuccessful_logins[host] = "Failed to log in"

    if unsuccessful_logins:
        """body = f"Unsuccessful SSH login attempts:\n{unsuccessful_logins}"
        send_email("SSH Login Failure Report", body,
                    GLOBAL_TEST_LOGIN_CONFIG["email_sender",
                    GLOBAL_TEST_LOGIN_CONFIG["email_recipients"],
                    GLOBAL_TEST_LOGIN_CONFIG["smtp_server"],
                    GLOBAL_TEST_LOGIN_CONFIG["smtp_port"],
                    GLOBAL_TEST_LOGIN_CONFIG["smtp_user"],
                    GLOBAL_TEST_LOGIN_CONFIG["smtp_password"]])"""
        if DEBUG:
            print(unsuccessful_logins)
            print("Report sent for unsuccessful logins.")
    else:
        if DEBUG:
            print("All logins successful.")

if __name__ == "__main__":
    if DEBUG:
        print("Using configuration:", GLOBAL_TEST_LOGIN_CONFIG)
    main()