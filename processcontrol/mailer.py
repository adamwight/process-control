from email.mime.text import MIMEText
import smtplib


class Mailer(object):
    def __init__(self, config):
        self.from_address = config.get("failmail/from_address")
        self.to_address = config.get("failmail/to_address")
        # FIXME: this is set to ensure one failmail per instance. Should
        # do something more sophisticated to collect all calls and send
        # the mail before exiting.
        self.sent_fail_mail = False

    def fail_mail(self, subject, body="Hope your wits are freshly sharpened!"):
        if self.sent_fail_mail:
            return

        msg = MIMEText(body)

        msg["Subject"] = "Fail Mail : " + subject
        msg["From"] = self.from_address
        msg["To"] = self.to_address

        mailer = smtplib.SMTP("localhost")
        mailer.sendmail(
            self.from_address,
            self.to_address,
            msg.as_string()
        )
        mailer.quit()
        # only send one failmail per instance
        self.sent_fail_mail = True
