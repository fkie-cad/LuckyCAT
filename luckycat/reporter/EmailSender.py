import subprocess


class EmailSender:
    def send_mail(self, email, recipient):
        subprocess.call(f"echo {email} | mail -s 'Fuzzing Stats' " + recipient, shell=True)

    def send_mails_to_all_recipients(self, email, recipients):
        for recipient in recipients:
            self.send_mail(email, recipient)
