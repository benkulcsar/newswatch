import logging
from datetime import datetime, timezone

import requests
import yaml
from bs4 import BeautifulSoup

from common.config import (
    get_extract_s3_prefix,
    get_request_headers,
    get_s3_bucket_name,
    get_sites_yaml_path,
)
from common.models import Filter, Site, SiteHeadlineList
from common.utils import (
    build_s3_key,
    coalesce_dict_values,
    convert_objects_to_json_string,
    upload_data_to_s3,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def load_sites_from_yaml(yaml_path: str) -> list[Site]:
    with open(yaml_path, "r") as stream:
        sites_from_yaml = yaml.safe_load(stream)
        return [Site(**site) for site in sites_from_yaml]


def scrape_url(url: str) -> BeautifulSoup:
    page = requests.get(url=url, headers=get_request_headers())
    return BeautifulSoup(markup=page.content, features="html.parser")


def extract_headline(bs: BeautifulSoup, filters: list[Filter]) -> set[str]:
    return {
        element.text
        for filter in filters
        for element in bs.find_all(
            name=filter.tag,
            attrs=coalesce_dict_values(filter.attrs, True),
        )
    }


def extract_headlines(site: Site) -> SiteHeadlineList:
    return SiteHeadlineList(
        name=site.name,
        timestamp=datetime.now(timezone.utc),
        headlines=extract_headline(
            bs=scrape_url(site.url),
            filters=site.filters,
        ),
    )


def get_site_headline_lists(sites: list[Site]) -> list[SiteHeadlineList]:
    logger.info(f"Sites to be scraped: {[site.name for site in sites]}")
    return [extract_headlines(site) for site in sites]


def extract():
    timestamp_at_start = datetime.now(timezone.utc)
    logger.info(f"Extracting headlines at {timestamp_at_start}")

    site_headline_lists = get_site_headline_lists(
        sites=load_sites_from_yaml(
            yaml_path=get_sites_yaml_path(),
        ),
    )

    extracted_data_jsonstring = convert_objects_to_json_string(site_headline_lists)
    object_key = build_s3_key(prefix=get_extract_s3_prefix(), timestamp=timestamp_at_start, extension="json")

    s3_response = upload_data_to_s3(
        bucket_name=get_s3_bucket_name(),
        key=object_key,
        data=extracted_data_jsonstring,
    )

    if s3_response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
        logger.info(f"Uploaded headlines to S3: {object_key}")


def lambda_handler(event, context):
    extract()


if __name__ == "__main__":
    logger.info("Running local version of extract.py")
    extract()
