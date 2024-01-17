from datetime import datetime
from enum import Enum
from typing import Literal

from entsoe.mappings import Area
from pydantic import Field

from power_stash.models.request import BaseRequest, BaseRequestBuilder


class RequestType(str, Enum):
    CONSUMPTION = "consumption"
    GENERATION = "generation"
    DAY_AHEAD_PRICE = "day-ahead price"
    INSTALLED_GENERATION_CAPACITY = "installed generation capacity"
    # TODO: extend to other request types.
    # EXCHANGES = "exchanges"
    # EXCHANGE_FORECAST = "exchange forecast"
    # GENERATION_FORECAST = "generation forecast"
    # CONSUMPTION_FORECAST = "consumption forecast"

    def __str__(self) -> str:  # noqa: D105
        return self.value


class EntsoeRequest(BaseRequest):
    area: Area = Field(description="Area, zone-key or country code.")
    request_type: RequestType = Field(description="type of data requested.")
    net_number: bool | None = Field(
        default=None,
        description="""
        Condense generation and consumption into a net number.
        Valid when `request_type=="generation"`.
        """,
    )
    resolution: Literal["60T", "30T", "15T"] | None = Field(
        default=None,
        description="""
        Either 60T for hourly values, 30T for half-hourly values or 15T for quarterly values.
        Valid when request_type="day-ahead price"
        """,
    )


class EntsoeRequestBuilder(BaseRequestBuilder):
    def __init__(self) -> None:
        self.areas = list(Area)
        self.request_types = list(RequestType)

    def build_default_requests(self, start: datetime, end: datetime) -> list[EntsoeRequest]:
        """Return all the default requests for the given dates.

        Download all areas as defined in enum Area,
        for all request_types defined in enum RequestType.
        """
        all_requests = []
        for area in self.areas[:1]:
            for request_type in self.request_types:
                new_request = EntsoeRequest(
                    start=start,
                    end=end,
                    area=area,
                    request_type=request_type,
                )
                all_requests.append(new_request)

        return all_requests
