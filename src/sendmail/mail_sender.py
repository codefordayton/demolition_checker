import os
import mailtrap as mt
from jinja2 import Template
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

   
    template = env.get_template("template.html")

    filled_template = template.render(record_number=args["record_number"], record_type=args["record_type"], project_name=args["project_name"], address=args["address"], record_link=args["record_link"])

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
        return {"error": f"Mailtrap authorization error {MAILTRAP_API_TOKEN}, {MAILTRAP_SENDER_ADDRESS}, {MAILTRAP_TO_ADDRESS}", "body": args, "filled_template": filled_template}

    return {"body": args}

    

    