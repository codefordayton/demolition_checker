import logging
import os
import mailtrap as mt
from jinja2 import Environment, FileSystemLoader, select_autoescape
from src.schema import BuildingServicesSearchResult, PermitType

env = Environment(
    loader=FileSystemLoader("src/sendmail"), autoescape=select_autoescape()
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def send_email(
    records: list[BuildingServicesSearchResult],
    start_date: str,
    permit_types: list[PermitType],
):
    MAILTRAP_API_TOKEN = os.environ.get("MAILTRAP_API_TOKEN")
    MAILTRAP_SENDER_ADDRESS = os.environ.get("MAILTRAP_SENDER_ADDRESS")
    MAILTRAP_TO_ADDRESS = os.environ.get("MAILTRAP_TO_ADDRESS")
    MAILTRAP_BCC_ADDRESS = os.environ.get("MAILTRAP_BCC_ADDRESS")
    MAILTRAP_CC_ADDRESS = os.environ.get("MAILTRAP_CC_ADDRESS")

    for env_var in (
        "MAILTRAP_API_TOKEN",
        "MAILTRAP_SENDER_ADDRESS",
        "MAILTRAP_TO_ADDRESS",
    ):
        if not os.environ.get(env_var):
            raise EnvironmentError(f"Required mailtrap variable {env_var} not set")

    mainTemplate = env.get_template("template.html")
    dataTemplate = env.get_template("record.html")

    # For each record, fill the data template, then put the data into the main template
    filled_template = mainTemplate.render(
        records=[dataTemplate.render(record=record) for record in records],
        permit_types=permit_types,
        start_date=start_date,
    )

    logger.debug(filled_template)

    mail = mt.Mail(
        sender=mt.Address(email=MAILTRAP_SENDER_ADDRESS, name="Code For Dayton"),
        to=[mt.Address(email=MAILTRAP_TO_ADDRESS)],
        subject="New demolition notice from the Demolition Spider",
        text="Please enable HTML to view this message",
        html=filled_template,
        category="Integration Test",
    )
    if MAILTRAP_CC_ADDRESS:
        mail.cc = [mt.Address(email=MAILTRAP_CC_ADDRESS)]
    if MAILTRAP_BCC_ADDRESS:
        mail.bcc = [mt.Address(email=MAILTRAP_BCC_ADDRESS)]

    # Send the email
    try:
        client = mt.MailtrapClient(token=MAILTRAP_API_TOKEN)
        client.send(mail)
    except mt.exceptions.AuthorizationError:
        # Handle the authorization error here
        return {
            "error": f"Mailtrap authorization error, {MAILTRAP_SENDER_ADDRESS}, {MAILTRAP_TO_ADDRESS}",
            "body": records,
            "filled_template": filled_template,
        }

    return {"body": records}
