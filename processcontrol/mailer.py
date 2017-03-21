from email.mime.text import MIMEText
import smtplib


class Mailer(object):
    def __init__(self, config):
        self.config = config
        # FIXME: this is set to ensure one failmail per instance. Should
        # do something more sophisticated to collect all calls and send
        # the mail before exiting.
        self.sent_fail_mail = False

    def fail_mail(self, subject, body="Hope your wits are freshly sharpened!"):
        if self.sent_fail_mail:
            return

        msg = MIMEText(body)

        msg["Subject"] = "Fail Mail : " + subject
        msg["From"] = self.config.get("from_address")
        msg["To"] = self.config.get("to_address")

        mailer = smtplib.SMTP("localhost")
        mailer.sendmail(
            self.config.get("from_address"),
            self.config.get("to_address"),
            msg.as_string()
        )
        mailer.quit()
        # only send one failmail per instance
        self.sent_fail_mail = True
