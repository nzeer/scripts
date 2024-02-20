import smtplib
from email.mime.text import MIMEText
from dataclasses import dataclass

@dataclass
class Email:
    sender: str
    recipient: str
    subject: str
    body: str

    def send(self):
        # ensure we have to/from addresses
        if self.sender is None:
            raise ValueError("No sender specified")
        elif self.recipient is None:
            raise ValueError("No recipient specified")
        
        # create the message
        msg = MIMEText(self.body)
        msg['Subject'] = self.subject
        msg['From'] = self.sender
        msg['To'] = self.recipient
        
        # send the message
        with smtplib.SMTP('localhost') as server:
            server.send_message(msg)
