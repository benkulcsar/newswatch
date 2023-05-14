import json
from collections.abc import Iterable
from datetime import datetime
from datetime import timezone

import boto3
import requests
import yaml
from bs4 import BeautifulSoup
from common.config import get_request_headers
from common.config import get_s3_bucket_name
from common.models import BsMatchFilter
from common.models import SiteHeadlineCollection
from common.models import SiteWithBsMatchFilters


def read_sites_with_bs_match_filters_from_yaml(sites_with_filters_yaml: str) -> list[SiteWithBsMatchFilters]:
    sites_with_bs_match_filters: list = []
    with open(sites_with_filters_yaml, "r") as stream:
        sites_from_yaml = yaml.safe_load(stream)
    for site_from_yaml in sites_from_yaml:
        sites_with_bs_match_filter = SiteWithBsMatchFilters(**site_from_yaml)
        sites_with_bs_match_filters.append(sites_with_bs_match_filter)

    return sites_with_bs_match_filters


def get_parsed_html_content_from_website(url: str) -> BeautifulSoup:
    headers = get_request_headers()
    page = requests.get(url=url, headers=headers)
    content = page.content

    parsed_content = BeautifulSoup(content, "html.parser")
    return parsed_content


def extract_headlines_from_html(parsed_html: BeautifulSoup, bs_match_filters: list[BsMatchFilter]) -> set[str]:
    extracted_headlines: set = set()
    for filter in bs_match_filters:
        tag = filter.tag
        if filter.attrs:
            attrs = {k: v or True for k, v in filter.attrs.items()}
        else:
            attrs = None
        filtered_elements = parsed_html.find_all(name=tag, attrs=attrs)
        filtered_headlines = [element.text for element in filtered_elements]
        extracted_headlines.update(filtered_headlines)
    return extracted_headlines


def convert_site_headline_collections_to_json_string(
    site_headline_collections: Iterable[SiteHeadlineCollection],
) -> str:
    return json.dumps([dict(records) for records in site_headline_collections], default=str)


def upload_data_to_s3(bucket_name: str, key: str, data: str) -> dict:
    s3 = boto3.client("s3")
    return s3.put_object(Bucket=bucket_name, Key=key, Body=data)


def extract():
    consistent_timestamp = datetime.now(timezone.utc)

    # Scrape
    sites_with_bs_match_filters = read_sites_with_bs_match_filters_from_yaml(
        sites_with_filters_yaml="src/sites-with-filters.yaml",
    )

    site_headline_collections = []

    for site in sites_with_bs_match_filters:
        parsed_html = get_parsed_html_content_from_website(url=site.url)
        extracted_headlines = extract_headlines_from_html(parsed_html=parsed_html, bs_match_filters=site.filters)

        site_headline_collections.append(
            SiteHeadlineCollection(
                name=site.name,
                timestamp=consistent_timestamp,
                headlines=extracted_headlines,
            ),
        )

    # Save
    ts = consistent_timestamp
    object_key = f"extracted-headlines/year={ts.year}/month={ts.month:02}/day={ts.day:02}/hour={ts.hour:02}.json"
    bucket_name = get_s3_bucket_name()

    payload = convert_site_headline_collections_to_json_string(site_headline_collections=site_headline_collections)

    _ = upload_data_to_s3(
        bucket_name=bucket_name,
        key=object_key,
        data=payload,
    )


if __name__ == "__main__":
    extract()
