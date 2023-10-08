import logging
import os

import requests
import yaml
from bs4 import BeautifulSoup

from common.models import Filter, Site, SiteHeadlines
from common.utils import (
    build_s3_key,
    coalesce_dict_values,
    convert_objects_to_json_string,
    get_current_timestamp,
    put_to_s3,
)


def load_sites_from_yaml(yaml_path: str) -> list[Site]:
    with open(yaml_path, "r") as stream:
        sites_from_yaml = yaml.safe_load(stream)
        return [Site(**site) for site in sites_from_yaml]


def scrape_url(url: str) -> BeautifulSoup:
    page = requests.get(url=url, headers=request_headers)
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
    return [extract_headlines(site) for site in sites]


def extract():
    timestamp_at_start = get_current_timestamp()
    logger.info(f"Extracting headlines at {timestamp_at_start}")

    site_headline_lists: list[SiteHeadlines] = get_site_headline_lists(
        sites=load_sites_from_yaml(
            yaml_path=sites_yaml_path,
        ),
    )

    object_key: str = build_s3_key(prefix=extract_s3_prefix, timestamp=timestamp_at_start, extension="json")

    s3_response: dict = put_to_s3(
        bucket_name=s3_bucket_name,
        key=object_key,
        data=convert_objects_to_json_string(site_headline_lists),
    )

    if s3_response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
        logger.info(f"Uploaded headlines to S3: {s3_bucket_name}/{object_key}")


# Lambda cold start


if logging.getLogger().hasHandlers():
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger()

request_headers = {
    "User-Agent": """Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) \
                            AppleWebKit/603.1 (KHTML, like Gecko) \
                            Chrome/117.0.0.0 Safari/537.36""",
}

s3_bucket_name = os.environ.get("S3_BUCKET_NAME", "")
extract_s3_prefix = os.environ.get("EXTRACT_S3_PREFIX", "")
sites_yaml_path = os.environ.get("SITES_YAML_PATH", "")


# Lambda handler


def lambda_handler(event, context):
    extract()
