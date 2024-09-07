from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from pydantic import ValidationError
from requests.models import Response

from common.models import Filter, Site
from extract import extract_headline, load_sites_from_yaml, scrape_url, REQUEST_HEADERS, REQUEST_GET_TIMEOUT_SEC


def test_load_sites_from_yaml(test_sites: list[Site]) -> None:
    sites: list[Site] = load_sites_from_yaml(
        yaml_path="tests/fixtures/sites-with-filters_yaml/valid.yaml",
    )
    assert sites == test_sites, "Sites loaded from YAML do not match expected sites"


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
    parsed_html: BeautifulSoup = scrape_url(url=test_url)

    mock_get.assert_called_with(url=test_url, headers=REQUEST_HEADERS, timeout=REQUEST_GET_TIMEOUT_SEC)
    assert parsed_html == BeautifulSoup(mock_response.content, "html.parser"), "Parsed HTML does not match expected"


@pytest.mark.parametrize("site_name, site_index", [("site1", 0), ("site3", 2), ("site4", 3)])
def test_extract_headline(
    site_name: str,
    site_index: int,
    test_sites: list[Site],
    test_headlines: dict[str, list[str]],
) -> None:
    with open(f"tests/fixtures/site_htmls/{site_name}.html", "r") as f:
        html = f.read()
    parsed_html = BeautifulSoup(html, "html.parser")
    bs_match_filters: list[Filter] = test_sites[site_index].filters
    headlines: list[str] = extract_headline(parsed_html, bs_match_filters)
    assert headlines == test_headlines[site_name], "Extracted headlines do not match expected"
