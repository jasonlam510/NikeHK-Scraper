from LoggerConfig import *
import smtplib
from email.message import EmailMessage
from smtplib import SMTPAuthenticationError
import ConfigManager
import sys

logger = logging.getLogger(__name__)
SAMPLE_CONFIG = {
    'sender_gmail' : {
        'gmail' : 'example@gmail.com',
        'password' : 'pw'
    },
    'receiver_list' : ['example0@gmail.com', 'example1@gmail.com'],
}
config = ConfigManager.load_config(SAMPLE_CONFIG)
gmail_user = config['sender_gmail']['gmail']
gmail_password = config['sender_gmail']['password']
to_email = config['receiver_list']

def boardcase_email(subject, body):
    # gmail_user = "jasonlamufobot@gmail.com"  # Your Gmail address
    # gmail_password = "zaap rkun mkhg slse"  # Your Gmail password or App Password

    for email in to_email:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = gmail_user
        msg['To'] = email

        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
            server.close()
            logger.info(f"Email sent to: {email}")
        except SMTPAuthenticationError as e:
            logger.error(f"{e}")
            raise e
        except Exception as e:
            logger.warning(f"{e}")

# Test
if __name__ == "__main__":
    logger = setup_logging()  
    boardcase_email('Test Notification', 'This is the body of the email')
