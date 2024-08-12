from dataclasses import dataclass
import json
from typing import Any
from scrapy import Spider
from scrapy.http import FormRequest, Response
from scrapy.utils.response import open_in_browser
from enum import Enum
from .sendmail import mail_sender


class PermitType(str, Enum):
    commercial_wrecking_permit = "Building/Wrecking/Commercial/NA"
    residential_wrecking_permit = "Building/Wrecking/Residential/NA"


@dataclass
class BuildingServicesSearchResult:
    # TODO validation (regex?)
    record_number: str  # e.g. WRK2024R-00138
    record_details_link: str  # URL to the record details page
    record_type: PermitType
    project_name: str | None
    address: str
    expiration_date: Any | None  # I haven't found any records w/ this yet
    short_notes: str | None

    def __str__(self):
        return f"{self.record_type.value}:\n{self.record_number} - {self.project_name} - {self.address}"


class DemolitionSpider(Spider):
    name = "DemolitionSpider"
    start_urls = [
        "https://aca-prod.accela.com/DAYTON/Cap/CapHome.aspx?module=Building&TabName=Building"
    ]
    custom_settings = {
        "LOG_LEVEL": "INFO"  # Default is DEBUG
    }

    permit_type: PermitType = PermitType.commercial_wrecking_permit
    start_date: str = "08/01/2023"  # strftime('%m/%d/%Y')
    open_in_browser: bool

    # TODO type checking around start_date, it should be a date not a str
    # TODO the results are actually paginated, so right now we're only grabbing the first page
    def __init__(
        self,
        permit_type: PermitType = None,
        start_date: str = None,
        open_in_browser: bool = False,
        *args,
        **kwargs,
    ):
        super(DemolitionSpider, self).__init__(*args, **kwargs)
        self.permit_type = permit_type or self.permit_type
        self.start_date = start_date or self.start_date
        self.open_in_browser = open_in_browser

    def parse(self, response: Response):
        form_data = {
            "ctl00$ScriptManager1": "ctl00$PlaceHolderMain$updatePanel|ctl00$PlaceHolderMain$btnNewSearch",
            "__EVENTTARGET": "ctl00$PlaceHolderMain$btnNewSearch",
            "ctl00$PlaceHolderMain$generalSearchForm$ddlGSPermitType": self.permit_type.value,
            "ctl00$PlaceHolderMain$generalSearchForm$txtGSStartDate": self.start_date,
        }
        self.logger.debug(f"FORMDATA:\n{json.dumps(form_data)}")
        form_data["__VIEWSTATE"] = response.css(
            "input#__VIEWSTATE::attr(value)"
        ).extract_first()

        yield FormRequest.from_response(
            response,
            formdata=form_data,
            clickdata={"id": "ctl00_PlaceHolderMain_btnNewSearch"},
            callback=self.parseResults,
        )

    def parseResults(self, response: Response):
        if self.open_in_browser:
            open_in_browser(response)

        results_empty = response.xpath(
            "//div[@id='ctl00_PlaceHolderMain_RecordSearchResultInfo_noDataMessageForSearchResultList_messageBar']"
        ).get()
        records_rows = response.xpath(
            "//table[@id='ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList']/tr"
        )

        # Make sure that the page format is as expected.
        # we expect that there's either no records with a message explaining that, or there are records without a message.
        # If that's not true, it's likely that the page format has changed and this spider needs to be updated.
        if results_empty and len(records_rows) > 0:
            raise Exception("Expected no records, but records were found")
        elif not results_empty and len(records_rows) == 0:
            raise Exception("Expected records, but none were found")

        # if there are records, extract them
        if records_rows:
            try:
                records = self.extract_records(response, records_rows)
                self.logger.info(f"Extracted {len(records)} records")
                for record in records:
                    self.logger.info(record)
            except Exception as e:
                self.logger.error(f"Error extracting records: {e}")
        else:
            self.logger.info("No records found")

    def extract_records(
        self, response: Response, records_rows
    ) -> list[BuildingServicesSearchResult]:
        records: list[BuildingServicesSearchResult] = []
        for row in records_rows:
            # if this row is a header row, skip it
            if row.xpath(".//th"):
                continue

            # if this row is the pagination row, skip it
            if row.xpath(".//table"):
                continue

            # convert the relative record_link to an absolute url
            record_link = response.urljoin(row.xpath(".//td[2]//a/@href").get())

            # select the data we want from the table row
            records.append(
                BuildingServicesSearchResult(
                    record_number=row.xpath("string(.//td[2])").get().strip(),
                    record_details_link=record_link,
                    # TODO parse this into PermitType from row.xpath("string(.//td[3])").get().strip()
                    record_type=self.permit_type,
                    project_name=row.xpath("string(.//td[4])").get().strip(),
                    address=row.xpath("string(.//td[5])").get().strip(),
                    expiration_date=row.xpath("string(.//td[6])").get().strip(),
                    short_notes=row.xpath("string(.//td[7])").get().strip(),
                )
            )
        mail_sender.send_email(records)
        return records
