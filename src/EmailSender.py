import asyncio
import sys,os
sys.path.append(os.getcwd())
from src.LoggerConfig import *
import src.ConfigManager as ConfigManager
import smtplib
from email.message import EmailMessage
from smtplib import SMTPAuthenticationError
import aiosmtplib


logger = logging.getLogger(__name__)
SAMPLE_CONFIG = {
    'sender_gmail' : {
        'gmail' : 'example@gmail.com',
        'password' : 'pw'
    },
    'receiver_list' : ['example0@gmail.com', 'example1@gmail.com'],
}
config = ConfigManager.load_config(SAMPLE_CONFIG)
GMAIL_USER = config['sender_gmail']['gmail']
GMAIL_PASSWORD = config['sender_gmail']['password']
TO_EMAIL = config['receiver_list']

async def async_boardcase_email(subject, body):
    for email in TO_EMAIL:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = GMAIL_USER
        msg['To'] = email

        try:
            smtp = aiosmtplib.SMTP(hostname='smtp.gmail.com', port=587)
            await smtp.connect()
            await smtp.login(GMAIL_USER, GMAIL_PASSWORD)
            await smtp.send_message(msg)
            await smtp.quit()
            logger.info(f"Email sent to: {email}")
        except SMTPAuthenticationError as e:
            logger.error(f"{e}")
            raise e
        except Exception as e:
            logger.warning(f"{e}")

async def async_broadcast_html_email(subject, html_body):
    for email in TO_EMAIL:
        msg = EmailMessage()
        msg.set_content(html_body, subtype='html')  # Set the HTML content
        msg['Subject'] = subject
        msg['From'] = GMAIL_USER
        msg['To'] = email

        try:
            smtp = aiosmtplib.SMTP(hostname='smtp.gmail.com', port=587)
            await smtp.connect()
            await smtp.login(GMAIL_USER, GMAIL_PASSWORD)
            await smtp.send_message(msg)
            await smtp.quit()
            logger.info(f"HTML email sent to: {email}")
        except SMTPAuthenticationError as e:
            logger.error(f"{e}")
            raise e
        except Exception as e:
            logger.warning(f"{e}")

async def async_send_email_with_image(subject, text, img_url):
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
    await async_broadcast_html_email(subject, html_content)

def boardcase_email(subject, body):
    for email in TO_EMAIL:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = GMAIL_USER
        msg['To'] = email

        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.send_message(msg)
            server.close()
            logger.info(f"Email sent to: {email}")
        except SMTPAuthenticationError as e:
            logger.error(f"{e}")
            raise e
        except Exception as e:
            logger.warning(f"{e}")


async def main():
    img_url = "https://static.nike.com.hk/resources/product/FQ8080-133/FQ8080-133_BL1.png"
    # await boardcase_email('Test Notification', 'This is the body of the email')
    await send_email_with_image("Test Email with Image", "This is a test email with an image.", img_url)

# Test
if __name__ == "__main__":
    logger = setup_logging()  
    # boardcase_email('Test Notification', 'This is the body of the email')
    asyncio.run(main())

    

