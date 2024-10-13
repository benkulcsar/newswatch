from datetime import datetime

from pydantic import BaseModel, HttpUrl, StrictStr


class Filter(BaseModel):
    """A filter to be applied to a BeautifulSoup object."""

    tag: StrictStr | None
    attrs: dict[str, str | None] | None


class Site(BaseModel):
    """Represents a website to be scraped with BeautifulSoup object filters"""

    name: StrictStr
    url: HttpUrl
    filters: list[Filter]


class SiteHeadlines(BaseModel):
    """Represents a list of headlines obtained from a website at a specific timestamp."""

    name: StrictStr
    timestamp: datetime
    headlines: list[StrictStr]


class WordFrequencies(BaseModel):
    """
    A dictionary of word frequencies stored as integers, representing percentages with
    four decimal places. For example, a percentage like 0.1025% is stored as 1025.
    """

    frequencies: dict[str, int]


class SiteWordFrequencies(WordFrequencies):
    """A dictionary of word frequencies for a specific site"""

    name: StrictStr


class LoadRecord(BaseModel):
    """A record to be loaded for consumption"""

    timestamp: str
    word: StrictStr
    frequency: int
