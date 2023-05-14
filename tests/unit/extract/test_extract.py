from unittest.mock import patch

import boto3
import moto
import pytest
from bs4 import BeautifulSoup
from extract import convert_site_headline_collections_to_json_string
from extract import extract_headlines_from_html
from extract import get_parsed_html_content_from_website
from extract import read_sites_with_bs_match_filters_from_yaml
from extract import upload_data_to_s3
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
    mock_response._content = b"<html><body><h2>Super Simple Site</h2></body></html>"

    mock_get.return_value = mock_response
    parsed_html = get_parsed_html_content_from_website(url=test_url)
    assert parsed_html == BeautifulSoup(mock_response.content, "html.parser")


@pytest.mark.parametrize("site_name, site_index", [("site1", 0), ("site3", 2), ("site4", 3)])
def test_extract_headlines_from_html(site_name, site_index, expected_sites_with_bs_match_filters, expected_headlines):
    with open(f"tests/unit/extract/site_htmls/{site_name}.html", "r") as f:
        html = f.read()
    parsed_html = BeautifulSoup(html, "html.parser")
    bs_match_filters = expected_sites_with_bs_match_filters[site_index].filters
    headlines = extract_headlines_from_html(parsed_html, bs_match_filters)
    assert headlines == expected_headlines[site_name]


def test_convert_site_headline_collections_to_json_string(site_headline_collections, expected_json_string):
    assert expected_json_string == convert_site_headline_collections_to_json_string(site_headline_collections)


@moto.mock_s3
def test_upload_data_to_s3(expected_json_string):
    bucket_name = "test-bucket"
    object_key = "test-object"

    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.create_bucket(Bucket=bucket_name)

    payload = expected_json_string
    response = upload_data_to_s3(
        bucket_name=bucket_name,
        key=object_key,
        data=payload,
    )

    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    object_body = s3_client.get_object(Bucket=bucket_name, Key=object_key)["Body"].read().decode("utf-8")
    assert object_body == payload
