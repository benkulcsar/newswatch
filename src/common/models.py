from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl, StrictStr


class Filter(BaseModel):
    """A filter to be applied to a BeautifulSoup object."""

    tag: Optional[StrictStr]
    attrs: Optional[dict[str, Optional[str]]]


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
    A dictionary of word frequencies expressed as percentages with four decimal places.
    In order to store these percentages as integers, the decimal point is shifted four places to the right.
    For example, a percentage like 0.1025% (or 0.001025) is represented as 1025 in the model.
    """

    frequencies: dict[str, int]


class SiteWordFrequencies(WordFrequencies):
    """A dictionary of word frequencies for a specific site"""

    name: StrictStr


class LoadRecord(BaseModel):
    """A record to be loaded for consumtion"""

    timestamp: str
    word: StrictStr
    frequency: int
