import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

DEBUG: bool = True

GLOBAL_TEST_LOGIN_CONFIG = {
    "results_csv_path": "./ping_unsuccessful_results.csv",
    "smtp_host": "af-smtp.us.af.mil",
    "smtp_port": 587,
    "smtp_user": "user@example.com",
    "smtp_pass": "password",
    "smtp_from": "wralc.tila.centra@us.af.mil",
    "smtp_to": ["robert.jackson.111.ctr@us.af.mil", "gregory.sanders.4.ctr@us.af.mil", "john.gray.29.ctr@us.af.mil"],
    "email_subject": "Unsuccessful login Attempts found",
}

def read_csv_file(file_path: str) -> list:
    results = []
    try:
        with open(file_path, mode='r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                results.append(row)
    except Exception as e:
        if DEBUG:
            print(f"Error reading CSV file: {e}")
    return results

def main():
    # Read the CSV file
    unsuccessful_attempts = []
    try:
        unsuccessful_attempts = read_csv_file(GLOBAL_TEST_LOGIN_CONFIG["results_csv_path"])
    except Exception as e:
        if DEBUG:
            print(f"Error reading CSV file: {e}")
            
    # Check if there are any unsuccessful attempts and send an email
    if unsuccessful_attempts:
        # Create the email
        msg = MIMEMultipart()
        msg['From'] = GLOBAL_TEST_LOGIN_CONFIG["smtp_from"]
        msg['To'] = ", ".join(GLOBAL_TEST_LOGIN_CONFIG["smtp_to"])
        msg['Subject'] = GLOBAL_TEST_LOGIN_CONFIG["email_subject"]

        # Email body
        body = "The following hosts were unreachable:\n\n"
        for attempt in unsuccessful_attempts:
            body += f"Host: {attempt['host']}, Status: {attempt['status']}\n"
        msg.attach(MIMEText(body, 'plain'))

        try:
            # Send the email
            with smtplib.SMTP(GLOBAL_TEST_LOGIN_CONFIG["smtp_host"], GLOBAL_TEST_LOGIN_CONFIG["smtp_port"]) as server:
                server.sendmail(GLOBAL_TEST_LOGIN_CONFIG["smtp_from"], GLOBAL_TEST_LOGIN_CONFIG["smtp_to"], msg.as_string())
            if DEBUG:
                print("Email sent to notify about unsuccessful ping attempts.")
        except Exception as e:
            if DEBUG:
                print(f"Error sending email: {e}")
    else:
        if DEBUG:
            print("No unsuccessful attempts found. No email sent.")
        
        
if __name__ == "__main__":
    main()
