import os
import mailtrap as mt
from jinja2 import Environment, FileSystemLoader, select_autoescape
from src.schema import BuildingServicesSearchResult

env = Environment(
    loader=FileSystemLoader("src/sendmail"),
    autoescape=select_autoescape()
)

def send_email(records: list[BuildingServicesSearchResult]):
    MAILTRAP_API_TOKEN = os.environ.get("MAILTRAP_API_TOKEN")
    MAILTRAP_SENDER_ADDRESS = os.environ.get("MAILTRAP_SENDER_ADDRESS") 
    MAILTRAP_TO_ADDRESS = os.environ.get("MAILTRAP_TO_ADDRESS")
    MAILTRAP_BCC_ADDRESS = os.environ.get("MAILTRAP_BCC_ADDRESS")
    MAILTRAP_CC_ADDRESS = os.environ.get("MAILTRAP_CC_ADDRESS")

    if not MAILTRAP_API_TOKEN:
        raise EnvironmentError("MAILTRAP_API_TOKEN env variable is not set")
    if not MAILTRAP_SENDER_ADDRESS:
        raise EnvironmentError("MAILTRAP_SENDER_ADDRESS env variable is not set")
    if not MAILTRAP_TO_ADDRESS:
        raise EnvironmentError("MAILTRAP_TO_ADDRESS env variable is not set")

   
    mainTemplate = env.get_template("template.html")
    dataTemplate = env.get_template("record.html")

    
    # For each record, fill the data template, then put the data into the main template
    filled_template = mainTemplate.render(
        records=[dataTemplate.render(record=record) for record in records]
    )

    # print(filled_template)

    mail = mt.Mail(
        sender=mt.Address(email=MAILTRAP_SENDER_ADDRESS, name="Code For Dayton"),
        to=[mt.Address(email=MAILTRAP_TO_ADDRESS)],
        cc=[mt.Address(email=MAILTRAP_CC_ADDRESS)],
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
        return {"error": f"Mailtrap authorization error, {MAILTRAP_SENDER_ADDRESS}, {MAILTRAP_TO_ADDRESS}", "body": records, "filled_template": filled_template}

    return {"body": records}

    

    