from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import HttpUrl
from pydantic import StrictStr


class BsMatchFilter(BaseModel):
    tag: Optional[StrictStr]
    attrs: Optional[dict[str, Optional[str]]]


class SiteWithBsMatchFilters(BaseModel):
    name: StrictStr
    url: HttpUrl
    filters: list[BsMatchFilter]


class SiteHeadlineCollection(BaseModel):
    name: StrictStr
    timestamp: datetime
    headlines: list[StrictStr]
