"""
Pydantic definitions of pipeline data models.
"""

from datetime import datetime

from pydantic import BaseModel, HttpUrl, StrictStr


class Filter(BaseModel):
    """Defines a filter for extracting elements from a BeautifulSoup object."""

    tag: StrictStr | None
    attrs: dict[str, str | None] | None


class Site(BaseModel):
    """Represents a website with URL and BeautifulSoup filters."""

    name: StrictStr
    url: HttpUrl
    filters: list[Filter]


class Headline(BaseModel):
    """Represents a news headline from a specific site."""

    site_name: StrictStr
    timestamp: datetime
    headline: StrictStr


class WordFrequency(BaseModel):
    """Represents a word's frequency at a specific extraction timestamp."""

    word: StrictStr
    frequency: int
    timestamp: datetime
