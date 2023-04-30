import os
from collections.abc import Iterable
from datetime import datetime
from datetime import timezone

import requests
import yaml
from bs4 import BeautifulSoup
from common.config import get_request_headers
from common.models import BsMatchFilter
from common.models import SiteHeadlineRecords
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
            attrs = {k: v or True for k, v in filter.attrs.items()}  # TO REVIEW
        else:
            attrs = None
        filtered_elements = parsed_html.find_all(name=tag, attrs=attrs)
        filtered_headlines = [element.text for element in filtered_elements]
        extracted_headlines.update(filtered_headlines)
    return extracted_headlines


def save_site_headlines(all_site_headline_records: Iterable[SiteHeadlineRecords]):
    ts = datetime.now(timezone.utc)
    filename = f"headlines-{ts.year}-{ts.month:02}-{ts.day:02}-{ts.hour:02}.json"

    try:
        os.remove(filename)
    except OSError:
        pass

    with open(filename, "a") as file:
        for record in all_site_headline_records:
            file.write(record.json())


def extract():
    sites_with_bs_match_filters = read_sites_with_bs_match_filters_from_yaml(
        sites_with_filters_yaml="src/sites-with-filters.yaml",
    )

    all_site_headline_records = []

    for site in sites_with_bs_match_filters:
        parsed_html = get_parsed_html_content_from_website(url=site.url)
        extracted_headlines = extract_headlines_from_html(parsed_html=parsed_html, bs_match_filters=site.filters)

        site_headline_records = SiteHeadlineRecords(
            name=site.name,
            timestamp=datetime.now(timezone.utc),
            headlines=extracted_headlines,
        )

        all_site_headline_records.append(site_headline_records)

    save_site_headlines(all_site_headline_records=all_site_headline_records)


if __name__ == "__main__":
    extract()
