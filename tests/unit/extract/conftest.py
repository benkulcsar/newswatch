import datetime

import pytest
from common.models import BsMatchFilter
from common.models import SiteHeadlineCollection
from common.models import SiteWithBsMatchFilters
from pydantic import HttpUrl
from pydantic.tools import parse_obj_as


@pytest.fixture
def expected_sites_with_bs_match_filters():
    return [
        SiteWithBsMatchFilters(
            name="site1",
            url=parse_obj_as(HttpUrl, "https://www.site1.com"),
            filters=[BsMatchFilter(tag="a", attrs={"href": "hey"})],
        ),
        SiteWithBsMatchFilters(
            name="site2",
            url=parse_obj_as(HttpUrl, "https://site2.com"),
            filters=[BsMatchFilter(tag="x", attrs={"keyonly": None})],
        ),
        SiteWithBsMatchFilters(
            name="site3",
            url=parse_obj_as(HttpUrl, "https://site3.co.uk"),
            filters=[BsMatchFilter(tag="p", attrs=None)],
        ),
        SiteWithBsMatchFilters(
            name="site4",
            url=parse_obj_as(HttpUrl, "https://site4.news"),
            filters=[
                BsMatchFilter(tag="h2", attrs=None),
                BsMatchFilter(tag="h3", attrs=None),
                BsMatchFilter(tag="h4", attrs=None),
            ],
        ),
        SiteWithBsMatchFilters(
            name="site5",
            url=parse_obj_as(HttpUrl, "https://site5.co"),
            filters=[BsMatchFilter(tag=None, attrs={"aaa": "AAA"}), BsMatchFilter(tag=None, attrs={"bbb": "BBB"})],
        ),
        SiteWithBsMatchFilters(
            name="site6",
            url=parse_obj_as(HttpUrl, "https://www.site6.com"),
            filters=[BsMatchFilter(tag="A", attrs={"B": "C"}), BsMatchFilter(tag="XX", attrs={"YY": "ZZ"})],
        ),
    ]


@pytest.fixture
def expected_headlines():
    return {
        "site1": set(["abc", "xyz", "123"]),
        "site3": set(["More p tags", "Hey ho, let's go!"]),
        "site4": set(["yes", "YES"]),
    }


@pytest.fixture
def site_headline_collections():
    return [
        SiteHeadlineCollection(
            name="abc",
            timestamp=datetime.datetime(2021, 10, 10, 10, 10, 10, tzinfo=datetime.timezone.utc),
            headlines=["abc", "xyz", "123"],
        ),
        SiteHeadlineCollection(
            name="def",
            timestamp=datetime.datetime(2022, 10, 10, 10, 10, 10, tzinfo=datetime.timezone.utc),
            headlines=["def", "zzz", "456"],
        ),
    ]


@pytest.fixture
def expected_json_string():
    return (
        """[{"name": "abc", "timestamp": "2021-10-10 10:10:10+00:00", "headlines": ["abc", "xyz", "123"]}, """
        """{"name": "def", "timestamp": "2022-10-10 10:10:10+00:00", "headlines": ["def", "zzz", "456"]}]"""
    )
