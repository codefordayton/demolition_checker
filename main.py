from scrapy.crawler import CrawlerProcess
from src.demolition_spider import DemolitionSpider

process = CrawlerProcess()
process.crawl(DemolitionSpider)
process.start()
