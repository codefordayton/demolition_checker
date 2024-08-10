from src.demolition_spider import DemolitionSpider, PermitType
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings

settings = get_project_settings()
configure_logging(settings)
runner = CrawlerRunner(settings)


@defer.inlineCallbacks
def crawl():
    yield runner.crawl(
        DemolitionSpider,
        permit_type=PermitType.commercial_wrecking_permit,
        start_date="08/01/2023",
    )
    yield runner.crawl(
        DemolitionSpider,
        permit_type=PermitType.residential_wrecking_permit,
        start_date="08/01/2023",
    )
    reactor.stop()


crawl()
reactor.run()
