from scrapy.crawler import CrawlerProcess
from src.demolition_spider import DemolitionSpider, PermitType

process = CrawlerProcess()
process.crawl(DemolitionSpider, permit_type=PermitType.residential_wrecking_permit, start_date='08/01/2023')
process.start()
