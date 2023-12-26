import sys,os
sys.path.append(os.getcwd())
from src.LoggerConfig import *
import src.ConfigManager as ConfigManager
import smtplib
from email.message import EmailMessage
from smtplib import SMTPAuthenticationError


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

def broadcast_html_email(subject, html_body):
    for email in to_email:
        msg = EmailMessage()
        msg.set_content(html_body, subtype='html')  # Set the HTML content
        msg['Subject'] = subject
        msg['From'] = gmail_user
        msg['To'] = email

        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
            server.close()
            logger.info(f"HTML email sent to: {email}")
        except SMTPAuthenticationError as e:
            logger.error(f"{e}")
            raise e
        except Exception as e:
            logger.warning(f"{e}")

def send_email_with_image(subject, text, img_url):
    # Construct the HTML content
    html_content = f"""
    <html>
        <body>
            <p>{text}</p>
            <img src="{img_url}" alt="Image">
        </body>
    </html>
    """

    # Call the function to send an HTML email
    broadcast_html_email(subject, html_content)


# Test
if __name__ == "__main__":
    logger = setup_logging()  
    # boardcase_email('Test Notification', 'This is the body of the email')

    img_url = "https://static.nike.com.hk/resources/product/FQ8080-133/FQ8080-133_BL1.png"
    send_email_with_image("Test Email with Image", "This is a test email with an image.", img_url)

