import os
import sys

import requests
import yaml
from bs4 import BeautifulSoup

from common.models import Filter, Site, SiteHeadlines
from common.utils import (
    build_s3_key,
    call_and_catch_error_with_logging,
    coalesce_dict_values,
    convert_objects_to_json_string,
    get_current_timestamp,
    get_logger,
    put_to_s3,
)


def load_sites_from_yaml(yaml_path: str) -> list[Site]:
    with open(yaml_path, "r") as stream:
        sites_from_yaml = yaml.safe_load(stream)
        return [Site(**site) for site in sites_from_yaml]


def scrape_url(url: str) -> BeautifulSoup:
    page = requests.get(url=url, headers=REQUEST_HEADERS, timeout=REQUEST_GET_TIMEOUT_SEC)
    return BeautifulSoup(markup=page.content, features="html.parser")


def extract_headline(bs: BeautifulSoup, filters: list[Filter]) -> list[str]:
    return sorted(
        list(
            {
                element.text
                for filter in filters
                for element in bs.find_all(
                    name=filter.tag,
                    attrs=coalesce_dict_values(filter.attrs, True),
                )
            },
        ),
    )


def extract_headlines(site: Site) -> SiteHeadlines:
    logger.info(f"Site to be scraped: {site.name}")
    return SiteHeadlines(
        name=site.name,
        timestamp=get_current_timestamp(),
        headlines=extract_headline(
            bs=scrape_url(site.url),
            filters=site.filters,
        ),
    )


def get_site_headline_lists(sites: list[Site]) -> list[SiteHeadlines]:
    logger.info(f"Sites to be scraped: {[site.name for site in sites]}")
    return [
        extracted_headlines
        for site in sites
        if (extracted_headlines := call_and_catch_error_with_logging(func=extract_headlines, logger=logger, site=site))
        is not None
    ]


def extract():
    timestamp_at_start = get_current_timestamp()
    logger.info(f"Extracting headlines at {timestamp_at_start}")

    site_headline_lists: list[SiteHeadlines] = get_site_headline_lists(
        sites=load_sites_from_yaml(
            yaml_path=sites_yaml_path,
        ),
    )

    object_key: str = build_s3_key(prefix=extract_s3_prefix, timestamp=timestamp_at_start, extension="json")
    site_headline_lists_json = convert_objects_to_json_string(site_headline_lists)

    if is_local and not is_pytest:
        breakpoint()

    else:
        s3_response: dict = put_to_s3(
            bucket_name=s3_bucket_name,
            key=object_key,
            data=site_headline_lists_json,
        )

        if s3_response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
            logger.info(f"Uploaded headlines to S3: {s3_bucket_name}/{object_key}")


# Lambda cold start


logger = get_logger()

REQUEST_GET_TIMEOUT_SEC = 10
REQUEST_HEADERS = {
    "User-Agent": """Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                            AppleWebKit/537.36 (KHTML, like Gecko) \
                            Chrome/127.0.0.0 Safari/537.36""",
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
