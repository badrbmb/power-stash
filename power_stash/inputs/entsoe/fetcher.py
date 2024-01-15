import pandas as pd
from entsoe import EntsoePandasClient

from power_stash.inputs.entsoe.config import EntsoeEnv
from power_stash.inputs.entsoe.request import EntsoeRequest, RequestType
from power_stash.models.fetcher import FetcherInterface

entsoe_env = EntsoeEnv()


class EntsoeFetcher(FetcherInterface):
    def __init__(self) -> None:
        self.client = EntsoePandasClient(
            api_key=entsoe_env.security_token.get_secret_value(),
        )

    def fecth_data(self, *, request: EntsoeRequest) -> pd.DataFrame:  # noqa: D102
        match request.request_type:
            case RequestType.CONSUMPTION:
                result = self.client.query_load(
                    country_code=request.area,
                    start=request.start,
                    end=request.end,
                )
            case RequestType.GENERATION:
                result = self.client.query_generation(
                    country_code=request.area,
                    start=request.start,
                    end=request.end,
                    nett=(request.net_number or False),
                    psr_type=None,  # all types
                )
            case RequestType.DAY_AHEAD_PRICE:
                result = self.client.query_day_ahead_prices(
                    country_code=request.area,
                    start=request.start,
                    end=request.end,
                    resolution=(request.resolution or "60T"),
                )
            case RequestType.INSTALLED_GENERATION_CAPACITY:
                result = self.client.query_installed_generation_capacity(
                    country_code=request.area,
                    start=request.start,
                    end=request.end,
                    psr_type=None,  # all types
                )
            case _:
                raise NotImplementedError(
                    f"fetch_data for request_type={request.request_type} not implemented!",
                )

        # convert to UTC and return
        return result.tz_convert("UTC")
