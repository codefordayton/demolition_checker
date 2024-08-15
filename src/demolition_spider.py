import logging
import re
from scrapy import Spider
from scrapy.http import FormRequest, Response
from scrapy.utils.response import open_in_browser
from .schema import BuildingServicesSearchResult, PermitType


class DemolitionSpider(Spider):
    name = "DemolitionSpider"
    start_urls = [
        "https://aca-prod.accela.com/DAYTON/Cap/CapHome.aspx?module=Building&TabName=Building"
    ]
    custom_settings = {
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",  # Hide deprecation warning
    }

    permit_type: PermitType = PermitType.commercial_wrecking_permit
    start_date: str = "08/01/2023"  # strftime('%m/%d/%Y')
    open_in_browser: bool
    # Extracted records are retrieved from this field after the spider has been closed
    records: list[BuildingServicesSearchResult] = []

    # TODO type checking around start_date, it should be a date not a str
    def __init__(
        self,
        permit_type: PermitType = None,
        start_date: str = None,
        open_in_browser: bool = False,
        *args,
        **kwargs,
    ):
        super(DemolitionSpider, self).__init__(*args, **kwargs)
        self.logger.setLevel(logging.INFO)
        self.permit_type = permit_type or self.permit_type
        self.start_date = start_date or self.start_date
        self.open_in_browser = open_in_browser
        self.records.clear()
        self.logger.info(
            f"Initializing spider with permit_type {self.permit_type.value} and start_date {self.start_date}"
        )

    def follow_postback(
        self,
        response: Response,
        event_target: str = "",
        event_argument: str = "",
        formdata: dict = None,
        **kwargs,
    ):
        """
        Follows an ASP.NET postback event
        """

        return FormRequest.from_response(
            response,
            formdata={
                "__EVENTTARGET": event_target,
                "__EVENTARGUMENT": event_argument,
                "__VIEWSTATE": response.css("input#__VIEWSTATE::attr(value)").get(),
                **(formdata or {}),
            },
            **kwargs,
        )

    def follow_postback_link(
        self,
        response: Response,
        href: str = "",
        **kwargs,
    ):
        """
        Parses and follows an ASP.NET postback link
        """

        m = re.search(
            r"__doPostBack\('(?P<event_target>.+)'\s*,\s*'(?P<event_argument>.*)'\)",
            href,
        )
        return self.follow_postback(
            response,
            event_target=m.group("event_target"),
            event_argument=m.group("event_argument"),
            **kwargs,
        )

    def parse(self, response: Response):
        yield self.follow_postback(
            response,
            event_target="ctl00$PlaceHolderMain$btnNewSearch",
            event_argument="",
            formdata={
                "ctl00$PlaceHolderMain$generalSearchForm$ddlGSPermitType": self.permit_type.value,
                "ctl00$PlaceHolderMain$generalSearchForm$txtGSStartDate": self.start_date,
            },
            callback=self.parse_search_results,
        )

    def parse_search_results(self, response: Response):
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
            # TODO this exception is raised when a single result is found
            raise Exception("Expected records, but none were found")

        if results_empty:
            self.logger.info("No records found")
            return

        records = self.extract_records(response, records_rows)
        self.records.extend(records)
        self.logger.info(f"Extracted {len(records)} records")
        for record in records:
            self.logger.info(record)

        # if there are more pages, follow the next page link
        next_button = response.xpath(
            "//td[@class='aca_pagination_td aca_pagination_PrevNext']/a[contains(text(), 'Next')]"
        )
        if next_button:
            yield self.follow_postback_link(
                response,
                href=next_button.xpath("@href").get(),
                callback=self.parseResults,
            )

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
        return records
