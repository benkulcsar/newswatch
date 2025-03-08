import os
import sys
from datetime import datetime

import requests
import yaml
from bs4 import BeautifulSoup

from common.models import Filter, Site, Headline
from common.utils import (
    build_s3_key,
    call_and_catch_error_with_logging,
    coalesce_dict_values,
    convert_objects_to_parquet_bytes,
    get_current_timestamp,
    get_logger,
    put_to_s3,
)

logger = get_logger()


def load_sites_from_yaml(yaml_path: str) -> list[Site]:
    """Load site structure configurations from a YAML file."""
    with open(yaml_path, "r") as stream:
        sites_from_yaml = yaml.safe_load(stream)
        return [Site(**site) for site in sites_from_yaml]


@call_and_catch_error_with_logging(logger=logger)
def scrape_url(url: str) -> BeautifulSoup:
    """Fetch and parse HTML content from a URL."""

    response = requests.get(url=url, headers=REQUEST_HEADERS, timeout=REQUEST_GET_TIMEOUT_SEC)
    content = response.content
    logger.info(f"{url} respone: {response.status_code}, received {len(content)} bytes")
    return BeautifulSoup(markup=content, features="html.parser")


def extract_headline_strings(bs: BeautifulSoup, filters: list[Filter]) -> list[str]:
    """Extract and return deduplicated headlines from HTML using given filters."""

    headlines: set[str] = {
        element.text
        for filter in filters
        for element in bs.find_all(
            name=filter.tag,
            attrs=coalesce_dict_values(filter.attrs, True),
        )
    }
    return sorted(list(headlines))


def get_headlines(sites: list[Site], timestamp: datetime) -> list[Headline]:
    """Scrape headlines from a list of sites and return them with timestamps."""

    logger.info(f"Sites to be scraped: {[site.name for site in sites]}")
    headlines: list[Headline] = []

    for site in sites:
        logger.info(f"Extracting from site: {site.name}")
        extracted_headlines = extract_headline_strings(bs=scrape_url(site.url), filters=site.filters)
        if extracted_headlines:
            site_headlines = [
                Headline(
                    site_name=site.name,
                    timestamp=timestamp,
                    headline=headline,
                )
                for headline in extracted_headlines
            ]
            headlines.extend(site_headlines)

    return headlines


def extract() -> None:
    """Extract headlines from news sites and upload them to S3 in parquet format."""

    timestamp_at_start = get_current_timestamp()
    logger.info(f"Extracting headlines at {timestamp_at_start}")

    sites: list[Site] = load_sites_from_yaml(yaml_path=sites_yaml_path)
    headlines: list[Headline] = get_headlines(sites=sites, timestamp=timestamp_at_start)

    object_key: str = build_s3_key(prefix=extract_s3_prefix, timestamp=timestamp_at_start, extension="parquet")
    headlines_parquet: bytes = convert_objects_to_parquet_bytes(headlines)

    if is_local and not is_pytest:
        test_s3_response: dict = put_to_s3(
            bucket_name=os.environ.get("TEST_S3_BUCKET_NAME"),
            key=os.environ.get("TEST_S3_EXTRACT_KEY"),
            data=headlines_parquet,
        )
        logger.info(test_s3_response)
        breakpoint()
        return

    s3_response: dict = put_to_s3(
        bucket_name=s3_bucket_name,
        key=object_key,
        data=headlines_parquet,
    )

    if s3_response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
        logger.info(f"Uploaded headlines to S3: {s3_bucket_name}/{object_key}")


# Lambda cold start

REQUEST_GET_TIMEOUT_SEC = 10
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.5",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1",
}


s3_bucket_name = os.environ.get("S3_BUCKET_NAME", "")
extract_s3_prefix = os.environ.get("EXTRACT_S3_PREFIX", "")
sites_yaml_path = os.environ.get("SITES_YAML_PATH", "")

is_local = os.environ.get("AWS_EXECUTION_ENV") is None
is_pytest = "pytest" in sys.modules

# Lambda handler


def lambda_handler(event, context):
    extract()


if is_local and not is_pytest and __name__ == "__main__":
    extract()
