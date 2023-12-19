import smtplib
from email.message import EmailMessage
to_email = ['']


def send_email(subject, body):
    gmail_user = ""  # Your Gmail address
    gmail_password = ""  # Your Gmail password or App Password

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

            print('Email sent!')
        except Exception as e:
            print('Something went wrong...', e)

# Test
if __name__ == "__main__":
    send_email('Update Notification', 'This is the body of the email')
