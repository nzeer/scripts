from datetime import datetime, timedelta
import os
import json
import matplotlib.pyplot as plt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

DEBUG: bool = True

# Expanded configuration to include SMTP settings and email details
GLOBAL_FSMON_CONFIG = {
    "plot_path": "./graphs/usage_chart.png",
    "log_files_path": "./dblog",
    "days_to_parse": 7,
    "smtp_host": "smtp.example.com",
    "smtp_port": 587,
    "smtp_user": "user@example.com",
    "smtp_pass": "password",
    "smtp_from": "user@example.com",
    "smtp_to": ["recipient1@example.com", "recipient2@example.com"],
    "email_subject": "File System Usage Report: {start_date} to {end_date}"
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
            usage_data.append((date, used_space))
    return usage_data

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

def send_email_with_graph(plot_path: str, email_config: dict):
    msg = MIMEMultipart()
    msg['From'] = email_config['smtp_from']
    msg['To'] = ", ".join(email_config['smtp_to'])
    msg['Subject'] = email_config['email_subject'].format(start_date=(datetime.now() - timedelta(days=email_config['days_to_parse'])).strftime('%Y-%m-%d'), end_date=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
    
    # Attach the plot image
    with open(plot_path, 'rb') as file:
        msg.attach(MIMEImage(file.read(), name=os.path.basename(plot_path)))
    
    try:
        with smtplib.SMTP(email_config['smtp_host'], email_config['smtp_port']) as server:
            server.starttls()
            server.login(email_config['smtp_user'], email_config['smtp_pass'])
            server.send_message(msg)
            if DEBUG:
                print("Email sent successfully.")
    except Exception as e:
        if DEBUG:
            print(f"Failed to send email: {e}")

if __name__ == "__main__":
    init_directories(os.path.dirname(GLOBAL_FSMON_CONFIG['plot_path']))
    init_directories(GLOBAL_FSMON_CONFIG['log_files_path'])
    usage_data = get_usage_data(GLOBAL_FSMON_CONFIG['log_files_path'], GLOBAL_FSMON_CONFIG['days_to_parse'])
    create_weekly_graph(usage_data, GLOBAL_FSMON_CONFIG['plot_path'])
    #send_email_with_graph(GLOBAL_FSMON_CONFIG['plot_path'], GLOBAL_FSMON_CONFIG)
