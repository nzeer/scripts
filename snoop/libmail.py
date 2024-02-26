import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field
import configparser
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load Configuration from INI File
config = configparser.ConfigParser()
try:
    config.read('config.ini')
    if not all(key in config['SSH'] for key in ['ansible_hosts_file', 'ssh_user', 'ssh_key_path']):
        raise ValueError("Missing essential SSH configuration.")
except Exception as e:
    logging.error(f"Failed to read or validate configuration file: {e}")
    exit(1)

@dataclass
class EmailConfig:
    sender: str
    recipients: list
    smtp_server: str
    smtp_port: int
    smtp_user: str
    smtp_password: str

    def send_email(self, subject: str, body: str):
        message = MIMEMultipart()
        message['From'] = self.sender
        message['To'] = ", ".join(self.recipients)
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.sender, self.recipients, message.as_string())
                logging.info("Email sent successfully.")
        except Exception as e:
            logging.error(f"Failed to send email: {e}")

# Initialize EmailConfig with values from the configuration file
email_config = EmailConfig(
    sender=config['Email']['email_sender'],
    recipients=config['Email']['email_recipients'].split(','),
    smtp_server=config['Email']['smtp_server'],
    smtp_port=config['Email'].getint('smtp_port'),
    smtp_user=config['Email']['smtp_user'],
    smtp_password=config['Email']['smtp_password']
)

# Example usage of EmailConfig to send an email
# This is where you would call email_config.send_email(subject, body) in your main script
# after determining the email subject and body based on your logic (e.g., after SSH tests)
subject = "Test Email Subject"
body = "This is a test email body."
email_config.send_email(subject, body)