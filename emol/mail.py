import smtplib, base64
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import base64

def enviar_mail(destinatario, asunto, mensaje, files=None):
    if type(destinatario) != list:
        destinatario = [destinatario]
    if type(files) != list:
        files = [files]
    msg = MIMEMultipart()
    msg['From'] = "NachoEmol"
    msg['To'] = COMMASPACE.join(destinatario)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = asunto

    msg.attach(MIMEText(mensaje))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
            part['Content-Disposition'] = (
                'attachment; filename="%s"' % basename(f))
            msg.attach(part)
            
    fromaddr = "mangadescarga@gmail.com"
    toaddr = destinatario
    username = "mangadescarga@gmail.com"
    password = base64.b64decode(b'bWFuZ2ExNDAxMDA=').decode("utf-8")
    server = smtplib.SMTP("smtp.gmail.com:587")
    server.ehlo()
    server.starttls()
    server.login(username,password)
    server.sendmail(fromaddr,toaddr,msg.as_string())
    server.quit()

if __name__ == "__main__":
    enviar_mail(
        "icastanedaw@gmail.com",
        "Descarga Capitulo - One Piece - 881 - A Wave Room",
        "One Piece - 881 - A Wave Room\n\nHan subido el capitulo y se ha descargado",
        "One Piece/881 - A Wave Room/01.jpg")
