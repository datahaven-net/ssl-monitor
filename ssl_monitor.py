import argparse
import datetime
import OpenSSL
import ssl
import smtplib
import json

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def get_expire_date(hostname):
    cert = ssl.get_server_certificate((hostname, 443))
    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
    timestamp = x509.get_notAfter().decode('utf-8').rstrip('Z')
    return datetime.datetime.strptime(timestamp, '%Y%m%d%H%M%S')


def send_email_notification(receiver_email, smtp_info, domain, days_left, expiration_date):
    text = """
This is an automatic notification.

The SSL certificate for the {} domain will expire in {} days.

Current certificate expiration date is {}.

Please take the necessary steps and renew your certificate to ensure the security of your server.
""".format(domain, days_left, expiration_date)

    html = """
<html>
  <body>
    <p>This is an automatic notification.</p>
    <p>The SSL certificate for the <b>{}</b> domain will expire in <b>{}</b> days.</p>
    <p>Current certificate expiration date is <b>{}</b></p>
    <p>Please take the necessary steps and renew your certificate to ensure the security of your server.</p>
  </body>
</html>
""".format(domain, days_left, expiration_date)

    message = MIMEMultipart("alternative")
    message["Subject"] = "%s certificate expires in %d days" % (domain, days_left, )
    message["From"] = smtp_info['from']
    message["To"] = receiver_email
    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP(smtp_info['host'], smtp_info['port'])
        # server.set_debuglevel(1)
        server.ehlo()
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
        server.login(smtp_info['user'], smtp_info['password'])
        server.sendmail(smtp_info['from'], receiver_email, message.as_string())
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        server.quit() 


def main():
    parser = argparse.ArgumentParser(
        prog='ssl_monitor',
        description='Monitoring tool for your SSL certificates, sends email notifications about expiring certificates',
        epilog='coded by Veselin Penev aka github.com/vesellov'
    )
    parser.add_argument(
        'domain',
        nargs='*',
        help='List of domain names to be monitored',
    )
    parser.add_argument(
        '-t', '--threshold',
        default=30,
        type=int,
        help='Number of days before expiration when notification should be sent',
    )
    parser.add_argument(
        '-e', '--emails',
        required=True,
        help='Comma-separated list of destination email addresses to receive notifications',
    )
    parser.add_argument(
        '-c', '--credentials',
        required=True,
        help='File path with JSON-formatted SMTP server details to be used for outgoing emails',
    )
    args = parser.parse_args()

    smtp_info = json.loads(open(args.credentials).read())

    for domain in args.domain:
        expire_date = get_expire_date(domain)
        days_before_expire = (expire_date - datetime.datetime.now()).days
        if days_before_expire < args.threshold:
            for email in args.emails.strip().split(','):
                send_email_notification(email.strip(), smtp_info, domain, days_before_expire, expire_date)


if __name__ == '__main__':
    main()
