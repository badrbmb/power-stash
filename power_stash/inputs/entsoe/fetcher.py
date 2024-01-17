import pandas as pd
from entsoe import EntsoePandasClient
from entsoe.exceptions import NoMatchingDataError
from requests import HTTPError

from power_stash.inputs.entsoe.config import EntsoeEnv
from power_stash.inputs.entsoe.request import EntsoeRequest, RequestType
from power_stash.models.fetcher import FetcherInterface

entsoe_env = EntsoeEnv()  # type: ignore

DEFAULT_RESOLUTION_DAY_HEAD_PRICE: str = "60T"

RETURN_NET_GENERATTION: bool = False


class EntsoeFetcher(FetcherInterface):
    def __init__(self) -> None:
        self.client = EntsoePandasClient(
            api_key=entsoe_env.security_token.get_secret_value(),
        )

    def fecth_data(self, *, request: EntsoeRequest) -> pd.DataFrame | None:  # noqa: D102
        _start = pd.to_datetime(request.start)
        _end = pd.to_datetime(request.end)
        match request.request_type:
            case RequestType.CONSUMPTION:
                result = self.client.query_load(
                    country_code=request.area,
                    start=_start,
                    end=_end,
                )
            case RequestType.GENERATION:
                result = self.client.query_generation(
                    country_code=request.area,
                    start=_start,
                    end=_end,
                    nett=(request.net_number or RETURN_NET_GENERATTION),
                    psr_type=None,  # all types
                )
            case RequestType.DAY_AHEAD_PRICE:
                try:
                    resolution = request.resolution or DEFAULT_RESOLUTION_DAY_HEAD_PRICE
                    result = self.client.query_day_ahead_prices(
                        country_code=request.area,
                        start=_start,
                        end=_end,
                        resolution=resolution,  # type: ignore (issue from the entsoe-py library ¯\_(ツ)_/¯)
                    )
                    result = pd.DataFrame(result, columns=["Day-ahead Price"])
                except NoMatchingDataError:
                    # the specified area does not have any results
                    result = None
                except HTTPError as e:
                    # the specified area does not have any results if bad request returned
                    if "Bad Request for url" not in str(e):
                        raise e
                    result = None

            case RequestType.INSTALLED_GENERATION_CAPACITY:
                # TODO: continue here why df is empty
                result = self.client.query_installed_generation_capacity(
                    country_code=request.area,
                    start=_start,
                    end=_end,
                    psr_type=None,  # all types
                )
            case _:
                raise NotImplementedError(
                    f"fetch_data for request_type={request.request_type} not implemented!",
                )

        # convert to UTC and return
        return result.tz_convert("UTC") if result is not None else None
