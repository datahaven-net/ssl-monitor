# ssl-monitor

Monitoring tool for your SSL certificates, sends email notifications about expiring certificates


        usage: ssl_monitor [-h] [-t THRESHOLD] -e EMAIL -c CREDENTIALS
                           [domain [domain ...]]

        Monitoring tool for your SSL certificates, sends email notifications about
        expiring certificates

        positional arguments:
          domain                List of domain names to be monitored

        optional arguments:
          -h, --help            show this help message and exit
          -t THRESHOLD, --threshold THRESHOLD
                                Number of days before expiration when notification
                                should be sent
          -e EMAIL, --email EMAIL
                                Destination email addresses to receive notifications
          -c CREDENTIALS, --credentials CREDENTIALS
                                File path with JSON-formatted SMTP server details to
                                be used for outgoing emails

        coded by Veselin Penev aka github.com/vesellov



## install

Clone the repository, create virtual environment and install pyOpenSSL:

        git clone https://github.com/datahaven-net/ssl-monitor.git
        cd ssl-monitor
        python -m venv venv
        ./venv/bin/pip install pyOpenSSL



## configure

Create a JSON file with details of your SMTP server to be used for outgoing emails:

        cat smtp.json
        {
            "from": "from-email@gmail.com",
            "host": "smtp.gmail.com",
            "port": 587,
            "user": "user",
            "password": "........",
        }



## setup a CRON task

The script can be directly executed via CRON task. For example to run SSL checks every day do:

        crontab -e

        0 0 * * * /home/user/ssl-monitor/venv/bin/python /home/user/ssl-monitor/ssl_monitor.py -e to-email@gmail.com -c /home/user/ssl-monitor/smtp.json my-first-server.com my-second-server.net my-another-host.org 1>>/tmp/ssl-monitor.log 2>>/tmp/ssl-monitor.err
