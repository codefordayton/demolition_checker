from dotenv import load_dotenv
from src.demolition_spider import DemolitionSpider, PermitType
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from src.sendmail import mail_sender
from scrapy import signals
import logging
import logging.config
from datetime import date
from datetime import timedelta

# N.B. that the ordering of these commands is intentional
settings = get_project_settings()
configure_logging(settings)

for module in [
    "scrapy.addons",
    "scrapy.core.engine",
    "scrapy.crawler",
    "scrapy.downloadermiddlewares.redirect",
    "scrapy.extensions.logstats",
    "scrapy.extensions.telnet",
    "scrapy.middleware",
    "scrapy.statscollectors",
    "urllib3.connectionpool",
]:
    logging.getLogger(module).setLevel(logging.WARN)

runner = CrawlerRunner(settings)
logger = logging.getLogger(__name__)


all_records = []


def spider_closed(spider, reason):
    global all_records
    logger.info(f"Spider closed: {spider.name}, reason: {reason}")
    if hasattr(spider, "records"):
        all_records.extend(spider.records)
        logger.info(
            f"Collected {len(spider.records)} records, total: {len(all_records)}"
        )
    else:
        logger.warning(f"Spider {spider.name} has no records attribute")


@defer.inlineCallbacks
def crawl(start_date: str, open_in_browser: bool, permit_types: list[PermitType]):
    for permit_type in permit_types:
        crawler = runner.create_crawler(DemolitionSpider)
        crawler.signals.connect(spider_closed, signal=signals.spider_closed)

        yield runner.crawl(
            crawler,
            permit_type=permit_type,
            start_date=start_date,
            open_in_browser=open_in_browser,
        )

    reactor.stop()


def main(start_date: str, open_in_browser: bool):
    permit_types = [
        PermitType.commercial_wrecking_permit,
        PermitType.residential_wrecking_permit,
    ]
    d = crawl(start_date, open_in_browser, permit_types)
    d.addCallback(lambda _: logger.info(f"All records: {len(all_records)}"))
    d.addCallback(
        lambda _: mail_sender.send_email(all_records, start_date, permit_types)
    )
    reactor.run()


if __name__ == "__main__":
    import argparse
    from os import path

    parser = argparse.ArgumentParser()
    # Note that start_date defaults to yesterday
    parser.add_argument(
        "--start_date",
        required=False,
        default=(date.today() - timedelta(days=1)).strftime("%m/%d/%Y"),
        help="Return permits submitted on or since this date",
    )
    parser.add_argument(
        "--open_in_browser",
        required=False,
        default=False,
        help="Open scraped results in browser",
    )
    args = parser.parse_args()

    # Load environment variables
    if path.isfile(".env.dev"):
        load_dotenv(dotenv_path=".env.dev")

    main(start_date=args.start_date, open_in_browser=args.open_in_browser)
