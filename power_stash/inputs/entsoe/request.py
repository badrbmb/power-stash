from enum import Enum
from typing import Literal

from entsoe.mappings import Area
from pydantic import Field

from power_stash.models.request import BaseRequest


class RequestType(str, Enum):
    CONSUMPTION = "consumption"
    GENERATION = "generation"
    DAY_AHEAD_PRICE = "day-ahead price"
    INSTALLED_GENERATION_CAPACITY = "installed generation capacity"
    EXCHANGES = "exchanges"
    EXCHANGE_FORECAST = "exchange forecast"
    GENERATION_FORECAST = "generation forecast"
    CONSUMPTION_FORECAST = "consumption forecast"

    def __str__(self) -> str:  # noqa: D105
        return self.value


class EntsoeRequest(BaseRequest):
    area: Area = Field(description="Area, zone-key or country code.")
    request_type: RequestType = Field(description="type of data requested.")
    net_number: bool | None = Field(
        default=None,
        description="When applicable, condense generation and consumption into a net number",
    )
    resolution: Literal["60T", "30T", "15T"] | None = Field(
        default=None,
        description="""
        When applicable, either 60T for hourly values, 30T for half-hourly values
        or 15T for quarterly values
        """,
    )
