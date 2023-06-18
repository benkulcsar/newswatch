from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl, StrictStr


class Filter(BaseModel):
    """A filter to be applied to a BeautifulSoup object."""

    tag: Optional[StrictStr]
    attrs: Optional[dict[str, Optional[str]]]


class Site(BaseModel):
    """A website to be scraped."""

    name: StrictStr
    url: HttpUrl
    filters: list[Filter]


class SiteHeadlineList(BaseModel):
    """A list of headlines from a website."""

    name: StrictStr
    timestamp: datetime
    headlines: list[StrictStr]


class WordCounts(BaseModel):
    """A list of word counts for a given timestamp."""

    timestamp: datetime
    word_counts: dict[str, int]
