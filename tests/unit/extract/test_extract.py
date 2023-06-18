from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from pydantic import ValidationError
from requests.models import Response

from extract import extract_headline, load_sites_from_yaml, scrape_url


def test_load_sites_from_yaml(expected_sites):
    sites = load_sites_from_yaml(
        yaml_path="tests/unit/extract/sites-with-filters_yaml/valid.yaml",
    )
    assert sites == expected_sites


@pytest.mark.parametrize("yaml", ["empty_filter.yaml", "not_string_filter.yaml"])
def test_load_sites_from_yaml_exception(yaml):
    with pytest.raises(ValidationError):
        _ = load_sites_from_yaml(
            yaml_path=f"tests/unit/extract/sites-with-filters_yaml/{yaml}",
        )


@patch("requests.get")
def test_scrape_url(mock_get):
    test_url = "http://test123abcxyz.io"
    mock_response = Response()
    mock_response._content = b"<html><body><h2>Super Simple Site</h2></body></html>"

    mock_get.return_value = mock_response
    parsed_html = scrape_url(url=test_url)
    assert parsed_html == BeautifulSoup(mock_response.content, "html.parser")


@pytest.mark.parametrize("site_name, site_index", [("site1", 0), ("site3", 2), ("site4", 3)])
def test_extract_headline(site_name, site_index, expected_sites, expected_headlines):
    with open(f"tests/unit/extract/site_htmls/{site_name}.html", "r") as f:
        html = f.read()
    parsed_html = BeautifulSoup(html, "html.parser")
    bs_match_filters = expected_sites[site_index].filters
    headlines = extract_headline(parsed_html, bs_match_filters)
    assert headlines == expected_headlines[site_name]
