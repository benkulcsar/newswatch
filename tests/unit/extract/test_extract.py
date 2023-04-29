from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from extract import extract_headlines_from_html
from extract import get_parsed_html_content_from_website
from extract import read_sites_with_bs_match_filters_from_yaml
from pydantic import ValidationError
from requests.models import Response


def test_read_sites_with_bs_match_filters_from_yaml(expected_sites_with_bs_match_filters):
    sites_with_bs_match_filters = read_sites_with_bs_match_filters_from_yaml(
        sites_with_filters_yaml="tests/unit/extract/sites-with-filters_yaml/valid.yaml",
    )
    assert sites_with_bs_match_filters == expected_sites_with_bs_match_filters


@pytest.mark.parametrize("yaml", ["empty_filter.yaml", "not_string_filter.yaml"])
def test_read_sites_with_bs_match_filters_from_yaml_exception(yaml):
    with pytest.raises(ValidationError):
        _ = read_sites_with_bs_match_filters_from_yaml(
            sites_with_filters_yaml=f"tests/unit/extract/sites-with-filters_yaml/{yaml}",
        )


@patch("requests.get")
def test_get_parsed_html_content_from_website(mock_get):
    test_url = "http://test123abcxyz.io"
    mock_response = Response()
    mock_response._content = "<html><body><h2>Super Simple Site</h2></body></html>"

    mock_get.return_value = mock_response
    parsed_html = get_parsed_html_content_from_website(url=test_url)
    assert parsed_html == BeautifulSoup(mock_response.content, "html.parser")


@pytest.mark.parametrize("site_name, site_index", [("site1", 0), ("site3", 2), ("site4", 3)])
def test_extract_headlines_from_html(site_name, site_index, expected_sites_with_bs_match_filters, expected_headlines):
    with open(f"/home/brownbear/projects/newswatch/tests/unit/extract/site_htmls/{site_name}.html", "r") as f:
        html = f.read()
    parsed_html = BeautifulSoup(html, "html.parser")
    bs_match_filters = expected_sites_with_bs_match_filters[site_index].filters
    headlines = extract_headlines_from_html(parsed_html=parsed_html, bs_match_filters=bs_match_filters)
    assert headlines == expected_headlines[site_name]


def test_save_site_headlines():
    # Temporary method to be replaced by saving to S3.
    # This is a placeholder for test driving the new function.
    assert True
