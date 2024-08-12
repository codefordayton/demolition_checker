from src.demolition_spider import DemolitionSpider, PermitType
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from src.sendmail import mail_sender
from scrapy import signals
import logging
from scrapy.utils.log import configure_logging

configure_logging(install_root_handler=False)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

settings = get_project_settings()
configure_logging(settings)
runner = CrawlerRunner(settings)

all_records = []

logger = logging.getLogger(__name__)

def spider_closed(spider, reason):
    global all_records
    logger.info(f"Spider closed: {spider.name}, reason: {reason}")
    if hasattr(spider, 'records'):
        all_records.extend(spider.records)
        logger.info(f"Collected {len(spider.records)} records, total: {len(all_records)}")
    else:
        logger.warning(f"Spider {spider.name} has no records attribute")

@defer.inlineCallbacks
def crawl():
    for permit_type in [PermitType.commercial_wrecking_permit, PermitType.residential_wrecking_permit]:
        crawler = runner.create_crawler(DemolitionSpider)
        crawler.signals.connect(spider_closed, signal=signals.spider_closed)
        yield runner.crawl(crawler, permit_type=permit_type, start_date="08/01/2023")

    reactor.stop()

def main():
    d = crawl()
    d.addCallback(lambda _: logger.info(f"All records: {len(all_records)}"))
    d.addCallback(lambda _: mail_sender.send_email(all_records))
    reactor.run()

if __name__ == "__main__":
    main()