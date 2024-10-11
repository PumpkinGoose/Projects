import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


#--TEST ONLY-----------------------------------------------------
def get_sender_creds():
    notify_email_creds = "/home/despegar/notify_email_creds.yaml"
    with open(notify_email_creds, "r") as file:
        sensitive = file.readlines()
        email = password = ""
        port = 0
    for line in sensitive:
        if "soc_mail_address" in line:
            email = line.split("=")[1].strip("\n")
        if "soc_mail_app_password" in line:
            password = line.split("=")[1].strip("\n")
        if "soc_mail_smtp_srv" in line:
            srv = line.split("=")[1].strip("\n")
        if "soc_mail_smtp_port" in line:
            port = int(line.split("=")[1].strip("\n"))
    return email, password, srv, port
#----------------------------------------------------------------

def send_email(dest_email, alert_name, body):
  with open('mail-footer.html', 'r') as file:
      mail_footer = file.read()
  subject = "Alerta SOC: " + alert_name.rstrip("_0")
  
  html_body = f"""
  <html>
  <head></head>
  <body>
  <h1>{subject}</h1>
  <p>{body}</p>
  <!-- Add an image for your signature -->
  {mail_footer}
  </body>
  </html>
  """
  
  #--TEST ONLY-----------------------------------------------------
  sender_email, sender_password, smtp_server, smtp_port = get_sender_creds()
  #----------------------------------------------------------------
  
  message = MIMEMultipart()
  message["From"] = sender_email
  message["To"] = dest_email
  message["Subject"] = subject
  message.attach(MIMEText(html_body, "html"))

  try:
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender_email, sender_passw)
    server.sendmail(sender_email, dest_email, message.as_string())
    server.quit()
    print("Email sent successfully")
  except Exception as e:
    print(f"An error occurred: {str(e)}")
