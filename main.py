import scrapy
from scrapy.http import FormRequest
from scrapy.utils.response import open_in_browser

class DemoSpider(scrapy.Spider):
    name = 'DemoSpider'
    start_urls = ['https://aca-prod.accela.com/DAYTON/Cap/CapHome.aspx?module=Building&TabName=Building']

    def parse(self, response):
        
        yield FormRequest.from_response(
            response,
            formdata = {
                'ctl00$ScriptManager1': 'ctl00$PlaceHolderMain$updatePanel|ctl00$PlaceHolderMain$btnNewSearch',
                '__EVENTTARGET': 'ctl00$PlaceHolderMain$btnNewSearch',
                'ctl00$PlaceHolderMain$generalSearchForm$ddlGSPermitType': 'Building/Wrecking/Residential/NA',
                'ctl00$PlaceHolderMain$generalSearchForm$txtGSStartDate': '08/01/2023', # TODO: this should be yesterday
                '__VIEWSTATE': response.css('input#__VIEWSTATE::attr(value)').extract_first()},
            clickdata={'id': 'ctl00_PlaceHolderMain_btnNewSearch'},
            callback=self.parseResults)
        # open_in_browser(response)

    def parseResults(self, response):
        test = response.xpath("//div[@id='ctl00_PlaceHolderMain_RecordSearchResultInfo_noDataMessageForSearchResultList_messageBar']")
        test2 = response.xpath("//table[@id='ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList']")
        print("RESULTS", test, test2)
        open_in_browser(response)
