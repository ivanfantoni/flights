import smtplib
import poplib
import imaplib
import email as e
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import parser
from html.parser import HTMLParser

class Email:
    def __init__(self, pop_server: str, server: str, port: int, user_name: str, user: str, password: str, mailto: str):
        self.server = server
        self.pop_server = pop_server
        self.port = port
        self.user_name = user_name
        self.user = user
        self.password = password
        self.mailto = mailto


    def send_email(self, subject: str, body: str, body_html: str, message_to = None):
        msg = MIMEMultipart('alternative')
        msg['subject'] = subject
        msg['from']  = self.user_name

        if message_to == None:
            msg['to'] = self.mailto
        else:
            msg['to'] = message_to
            self.mailto = message_to

        part1 = MIMEText(body, 'plain')
        msg.attach(part1)
        if body_html != None:
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)
        else:
            part2 = None

        mail = smtplib.SMTP(self.server, self.port)
        mail.ehlo()
        mail.starttls()
        mail.login(self.user, self.password)
        mail.sendmail(self.user, self.mailto.split(','), msg.as_string())
        mail.quit()


    def read_email_pop3(self):
        self.mailserver_pop = poplib.POP3_SSL(self.pop_server)
        self.mailserver_pop.user(self.user)
        self.mailserver_pop.pass_(self.password)
        
        _, items, _ = self.mailserver_pop.list()

        emails = []

        for message in items:
            id, _ = message.decode('utf-8').split(' ')
            _, text, _ = self.mailserver_pop.retr(id)
            decoded = b'\n'.join(text).decode('utf-8')
            fins = parser.Parser().parsestr(decoded)

            if fins.is_multipart():
                for part in fins.get_payload():
                    if part.get_content_type() == 'text/plain':
                        content = part.get_payload()

            email = { 
                'Message-Count': id,
                'Message-ID': fins.get('Message-ID'),
                'From' : fins.get('Return-Path')[1:-1],
                'To' : fins.get('To'),
                'Subject' : fins.get('Subject'),
                'Text': content,
                'Date' : fins.get('Date'),
            }
            emails.append(email)
        
        return emails

    def read_email(self):
        self.mailserver = imaplib.IMAP4_SSL(self.pop_server)
        self.mailserver.login(self.user, self.password)
        self.mailserver.select()
        
        _, items = self.mailserver.search(None, 'ALL')

        emails = []

        for id in items[0].split():
            _, texts = self.mailserver.fetch(id, '(RFC822)')

            for text in texts:
                if isinstance(text, tuple):
                    decoded = text[1].decode('utf-8')
                    fins = e.message_from_string(decoded)                    
        
                    if fins.is_multipart():
                        for part in fins.get_payload():
                            if part.get_content_type() == 'text/plain':
                                content = part.get_payload()


                    email = { 
                        'Message-Count': id,
                        'Message-ID': fins['Message-ID'],
                        'From' : fins['From'].split()[-1][1:-1],
                        'To' : fins['To'],
                        'Subject' : fins['Subject'],
                        'Text': content,
                        'Date' : fins['Date'],
                    }
                    emails.append(email)
        
        return emails



    def delete_email(self, message_id: str=None):
        list = self.read_email()

        for mail in list:  
            if str(mail['Message-ID']) == message_id:
                self.mailserver.store(mail['Message-Count'], '+FLAGS', '\\Deleted')
        self.mailserver.expunge()


    def close(self):
        self.mailserver.close()