import os
import mailtrap as mt
from jinja2 import Environment, FileSystemLoader, select_autoescape
env = Environment(
    loader=FileSystemLoader("src/sendmail"),
    autoescape=select_autoescape()
)

def send_email(args):
    MAILTRAP_API_TOKEN = os.environ.get("MAILTRAP_API_TOKEN")
    MAILTRAP_SENDER_ADDRESS = os.environ.get("MAILTRAP_SENDER_ADDRESS") 
    MAILTRAP_TO_ADDRESS = os.environ.get("MAILTRAP_TO_ADDRESS")
    MAILTRAP_BCC_ADDRESS = os.environ.get("MAILTRAP_BCC_ADDRESS")

   
    mainTemplate = env.get_template("template.html")
    dataTemplate = env.get_template("record.html")

    templates = []
    
    # For each record, fill the data template, then put the data into the main template
    for record in args:    
        templates.append(dataTemplate.render(record=record))


    filled_template = mainTemplate.render(records=templates)

    # print(filled_template)

    mail = mt.Mail(
        sender=mt.Address(email=MAILTRAP_SENDER_ADDRESS, name="Code For Dayton"),
        to=[mt.Address(email=MAILTRAP_TO_ADDRESS)],
        bcc=[mt.Address(email=MAILTRAP_BCC_ADDRESS)],
        subject="New demolition notice from the Demolition Spider",
        text="Please enable HTML to view this message",
        html=filled_template,
        category="Integration Test",
    )
    try:
        client = mt.MailtrapClient(token=MAILTRAP_API_TOKEN)
        client.send(mail)
    except mt.exceptions.AuthorizationError as e:
        # Handle the authorization error here
        return {"error": f"Mailtrap authorization error, {MAILTRAP_SENDER_ADDRESS}, {MAILTRAP_TO_ADDRESS}", "body": args, "filled_template": filled_template}

    return {"body": args}

    

    