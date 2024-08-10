from scrapy import Spider
from scrapy.http import FormRequest
from scrapy.utils.response import open_in_browser
from enum import Enum


class PermitType(str, Enum):
    commercial_wrecking_permit = 'Building/Wrecking/Commercial/NA'
    residential_wrecking_permit = 'Building/Wrecking/Residential/NA'

class DemolitionSpider(Spider):
    name = 'DemolitionSpider'
    start_urls = ['https://aca-prod.accela.com/DAYTON/Cap/CapHome.aspx?module=Building&TabName=Building']
    permit_type: PermitType = PermitType.commercial_wrecking_permit
    start_date: str = '08/01/2023' # strftime('%m/%d/%Y')
    
    # TODO type checking around start_date, it should be a date not a str
    def __init__(self, permit_type: PermitType = None, start_date: str = None, *args, **kwargs):
        super(DemolitionSpider, self).__init__(*args, **kwargs)
        if permit_type:
            self.permit_type = permit_type
        if start_date:
            self.start_date = start_date

    def parse(self, response):
        form_data = {
                'ctl00$ScriptManager1': 'ctl00$PlaceHolderMain$updatePanel|ctl00$PlaceHolderMain$btnNewSearch',
                '__EVENTTARGET': 'ctl00$PlaceHolderMain$btnNewSearch',
                'ctl00$PlaceHolderMain$generalSearchForm$ddlGSPermitType': self.permit_type.value,
                'ctl00$PlaceHolderMain$generalSearchForm$txtGSStartDate': self.start_date,
        }
        print(f"Setting the following formdata:\n{form_data}")
        form_data['__VIEWSTATE'] = response.css('input#__VIEWSTATE::attr(value)').extract_first()

        yield FormRequest.from_response(
            response,
            formdata = form_data,
            clickdata={'id': 'ctl00_PlaceHolderMain_btnNewSearch'},
            callback=self.parseResults)
        # open_in_browser(response)

    def parseResults(self, response):
        open_in_browser(response)
        
        results_empty = response.xpath("//div[@id='ctl00_PlaceHolderMain_RecordSearchResultInfo_noDataMessageForSearchResultList_messageBar']").get()
        records_rows = response.xpath("//table[@id='ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList']/tr")

        # Make sure that the page format is as expected.
        # we expect that there's either no records with a message explaining that, or there are records without a message.
        # If that's not true, it's likely that the page format has changed and this spider needs to be updated.
        if results_empty:
            assert len(records_rows) == 0, "Expected no records, but records were found"
        else:
            assert len(records_rows) > 0, "Expected records, but none were found"

        # if there are records, extract them
        if records_rows:
            records = self.extractRecords(response, records_rows)
            for record in records:
                print(record)


    def extractRecords(self, response, records_rows):
        records = []
        for row in records_rows:
            # if this row is a header row, skip it
            if row.xpath(".//th"):
                continue

            # if this row is the pagination row, skip it
            if row.xpath(".//table"):
                continue

            # select the data we want from the table row
            record_number = row.xpath("string(.//td[2])").get().strip()
            record_link = row.xpath(".//td[2]//a/@href").get()
            record_type = row.xpath("string(.//td[3])").get().strip()
            project_name = row.xpath("string(.//td[4])").get().strip()
            address = row.xpath("string(.//td[5])").get().strip()

            # make sure that the data is as expected
            assert record_number, "Record number not found"
            assert record_link, "Record link not found"
            assert record_type, "Record type not found"
            assert address, "Address not found"

            # convert the relative record_link to an absolute url
            record_link = response.urljoin(record_link)

            records.append({
                'record_number': record_number,
                'record_type': record_type,
                'project_name': project_name,
                'address': address,
                'record_link': record_link
            })


        # make sure that we actually extracted some records and it was a valid table
        assert records, "No records found in table"
        return records
