from datetime import datetime
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from pydantic import ValidationError
from requests.models import Response

from newswatch.common.models import Filter, Headline, Site
from newswatch.extract import (
    REQUEST_GET_TIMEOUT_SEC,
    REQUEST_HEADERS,
    extract_headline_strings,
    get_headlines,
    load_sites_from_yaml,
    scrape_url,
)


def test_load_sites_from_yaml(test_sites: list[Site]) -> None:
    expected_sites = test_sites

    loaded_sites: list[Site] = load_sites_from_yaml(
        yaml_path="tests/fixtures/sites-with-filters_yaml/valid.yaml",
    )

    assert loaded_sites == expected_sites, "Sites loaded from YAML do not match expected sites"


@pytest.mark.parametrize("yaml", ["empty_filter.yaml", "not_string_filter.yaml"])
def test_load_sites_from_yaml_exception(yaml: str) -> None:
    with pytest.raises(ValidationError):
        _ = load_sites_from_yaml(
            yaml_path=f"tests/fixtures/sites-with-filters_yaml/{yaml}",
        )


@patch("requests.get")
def test_scrape_url(mock_get) -> None:
    test_url = "http://test123abcxyz.io"
    mock_response = Response()
    mock_response._content = b"<html><body><h2>Super Simple Site</h2></body></html>"
    mock_get.return_value = mock_response
    expected_html = BeautifulSoup(mock_response.content, "html.parser")

    parsed_html: BeautifulSoup = scrape_url(url=test_url)

    mock_get.assert_called_with(url=test_url, headers=REQUEST_HEADERS, timeout=REQUEST_GET_TIMEOUT_SEC)
    assert parsed_html == expected_html, "Parsed HTML does not match expected"


@pytest.mark.parametrize("site_name, site_index", [("site1", 0), ("site3", 2), ("site4", 3)])
def test_extract_headline_strings(
    site_name: str,
    site_index: int,
    test_sites: list[Site],
    test_headlines: dict[str, list[str]],
) -> None:
    with open(f"tests/fixtures/site_htmls/{site_name}.html", "r") as f:
        html = f.read()
    parsed_html = BeautifulSoup(html, "html.parser")
    bs_match_filters: list[Filter] = test_sites[site_index].filters
    expeceted_headline_strings = test_headlines[site_name]

    extracted_headline_strings: list[str] = extract_headline_strings(parsed_html, bs_match_filters)

    assert extracted_headline_strings == expeceted_headline_strings, "Extracted headlines do not match expected"


def test_get_headlines(test_sites: list[Site], test_timestamp: datetime):
    with patch("newswatch.extract.extract_headline_strings", return_value=["foo", "bar"]), patch(
        "newswatch.extract.scrape_url",
    ):
        expected_headlines = [
            Headline(site_name=site.name, timestamp=test_timestamp, headline=headline)
            for site in test_sites
            for headline in ["foo", "bar"]
        ]

        extracted_headlines = get_headlines(sites=test_sites, timestamp=test_timestamp)

        assert extracted_headlines == expected_headlines
