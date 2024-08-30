import time
import argparse
import datetime
import OpenSSL
import ssl
import smtplib
import json
import traceback

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def get_expire_date(hostname, port_number=443):
    print('     checking', hostname, port_number)
    cert = ssl.get_server_certificate((hostname, port_number))
    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
    timestamp = x509.get_notAfter().decode('utf-8').rstrip('Z')
    return datetime.datetime.strptime(timestamp, '%Y%m%d%H%M%S')


def send_email_notification(receiver_email, smtp_info, domain, days_left=None, expiration_date=None, err=None):
    text = ""
    html = ""
    if expiration_date and days_left:
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

    if err:
        text = """
This is an automatic notification.

The SSL certificate for the {} domain was not verified because of the error: {}
""".format(domain, str(err))
        html = """
<html>
  <body>
    <p>This is an automatic notification.</p>
    <p>The SSL certificate for the {} domain was not verified because of an error: <b>{}</b>
  </body>
</html>
""".format(domain, str(err))


    message = MIMEMultipart("alternative")
    if days_left:
        message["Subject"] = "%s certificate expires in %d days" % (domain, days_left, )
    else:
        message["Subject"] = "%s certificate was not verified due to an error" % domain
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
        description='''Monitoring tool for your SSL certificates.

This script is originally intended to be started by linux CRON scheduler.
It will run a SSL verification call for each host listed in the input list of domain names.
You can also provide an alternative port number to be used for domain SSL verification request,
for example "first-server.net another-server.com:443 third-server.org:20443".

When SSL certificate expiry date is about to happen soon, script will send
a email notification mentioning the expiring certificate.
''',
        epilog='''You will have to provide SMTP configuration and credentials to be able to send emails.
Create a text file and use example from the README.md file to create your own JSON-formatted SMTP config file.
This script was coded by Veselin Penev aka github.com/vesellov
''',
    )
    parser.add_argument(
        'domain',
        nargs='*',
        help='List of domain names to be monitored (you can also add a port number)',
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

    print('started', time.asctime(), 'threshold is', args.threshold)
    for domain in args.domain:
        port_number = 443
        if domain.count(':'):
            domain, port_number = domain.split(':')
            port_number = int(port_number)
        try:
            expire_date = get_expire_date(domain, port_number=port_number)
        except Exception as e:
            print('  ERROR', domain, e)
            traceback.print_exc()
            for email in args.emails.strip().split(','):
                print('      sending email to', email)
                send_email_notification(email.strip(), smtp_info, domain, err=e)
            continue
        days_before_expire = (expire_date - datetime.datetime.now()).days
        print('  ', domain, 'expire in', days_before_expire, 'days')
        if days_before_expire < args.threshold:
            for email in args.emails.strip().split(','):
                print('      sending email to', email)
                send_email_notification(email.strip(), smtp_info, domain, days_before_expire, expire_date)


if __name__ == '__main__':
    main()
