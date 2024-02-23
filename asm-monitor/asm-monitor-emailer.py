from datetime import datetime, timedelta
import os
import json
import matplotlib.pyplot as plt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

DEBUG: bool = False

# Expanded configuration to include SMTP settings and email details
GLOBAL_FSMON_CONFIG = {
    "plot_path": "/usr/local/scripts/asm-monitor/graphs/usage_chart.png",
    "log_files_path": "/usr/local/scripts/asm-monitor/dblogs",
    "days_to_parse": 7,
    "smtp_host": "af-smtp.us.af.mil",
    "smtp_port": 587,
    "smtp_user": "user@example.com",
    "smtp_pass": "password",
    "smtp_from": "wralc.tila.centra@us.af.mil",
    "smtp_to": ["robert.jackson.111.ctr@us.af.mil", "gregory.sanders.4.ctr@us.af.mil", "john.gray.29.ctr@us.af.mil"],
    "email_subject": "9018v File System Usage Report: {start_date} to {end_date}",
}

def init_directories(directory_path: str):
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            if DEBUG:
                print(f"Directory created: {directory_path}")
    except Exception as e:
        if DEBUG:
            print(f"Error creating directory {directory_path}: {e}")

def load_db_data(log_file_path) -> dict:
    try:
        with open(log_file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        if DEBUG:
            print(f"The file {log_file_path} does not exist.")
        return {}

def get_usage_data(log_files_path: str, days: int=7) -> list:
    usage_data = []
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        log_file_name = date.strftime('%Y-%m-%d') + '.log'
        log_file_path = os.path.join(log_files_path, log_file_name)
        log_data = load_db_data(log_file_path)
        if log_data:
            total_space = round(log_data["total"], 2)
            used_space = round(total_space - log_data["free"], 2)
            usage_data.append((date, used_space, total_space))
    return usage_data

def create_weekly_graph2(usage_data: list, plot_path: str):
    if not usage_data:
        if DEBUG:
            print("No usage data available to plot.")
        return
    dates = [data[0] for data in usage_data]
    used_space = [data[1] for data in usage_data]
    total_space = [data[2] for data in usage_data]  # Extract total space data

    plt.figure(figsize=(10, 6))
    plt.plot(dates, used_space, marker='o', label='Used Space (GB)')
    plt.plot(dates, total_space, marker='x', linestyle='--', label='Total Space (GB)')
    plt.xlabel('Date')
    plt.ylabel('Space (GB)')
    plt.title('File System Usage and Total Space for the Week')
    plt.legend()
    plt.grid(True)
    plt.gcf().autofmt_xdate()
    plt.savefig(plot_path)
    plt.close()
    if DEBUG:
        print(f"Graph saved to {plot_path}")

def create_weekly_graph(usage_data: list, plot_path: str):
    if not usage_data:
        if DEBUG:
            print("No usage data available to plot.")
        return

    dates = [data[0] for data in usage_data]
    usages = [data[1] for data in usage_data]

    plt.figure(figsize=(10, 5))
    plt.plot(dates, usages, marker='o')
    plt.xlabel('Date')
    plt.ylabel('Usage (GB)')
    plt.title('File System Usage for the Week')
    plt.grid(True)
    plt.gcf().autofmt_xdate()
    plt.savefig(plot_path)
    plt.close()
    if DEBUG:
        print(f"Graph saved to {plot_path}")

def send_email(message):
    # Create a SMTP object and connect to the mail server
    smtp = smtplib.SMTP(GLOBAL_FSMON_CONFIG['smtp_host'])
    # Send the message to the recipients
    smtp.send_message(message)
    # Close the connection
    smtp.quit()


def send_email_with_graph(plot_path: str, email_config: dict):
    msg = MIMEMultipart()
    msg['From'] = email_config['smtp_from']
    msg['To'] = ", ".join(email_config['smtp_to'])
    msg['Subject'] = email_config['email_subject'].format(start_date=(datetime.now() - timedelta(days=email_config['days_to_parse'])).strftime('%Y-%m-%d'), end_date=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))

    # Attach the plot image
    with open(plot_path, 'rb') as file:
        msg.attach(MIMEImage(file.read(), name=os.path.basename(plot_path)))

    try:
        send_email(msg)
        if DEBUG:
            print("Email sent successfully.")
    except Exception as e:
        if DEBUG:
            print(f"Failed to send email: {e}")

if __name__ == "__main__":
    init_directories(os.path.dirname(GLOBAL_FSMON_CONFIG['plot_path']))
    init_directories(GLOBAL_FSMON_CONFIG['log_files_path'])
    usage_data = get_usage_data(GLOBAL_FSMON_CONFIG['log_files_path'], GLOBAL_FSMON_CONFIG['days_to_parse'])
    create_weekly_graph2(usage_data, GLOBAL_FSMON_CONFIG['plot_path'])
    send_email_with_graph(GLOBAL_FSMON_CONFIG['plot_path'], GLOBAL_FSMON_CONFIG)