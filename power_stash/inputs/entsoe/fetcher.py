import pandas as pd
import structlog
from entsoe import Area, EntsoePandasClient
from entsoe.exceptions import NoMatchingDataError
from entsoe.misc import year_blocks
from entsoe.parsers import parse_generation
from pandas.tseries.offsets import YearBegin, YearEnd
from requests import HTTPError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
)

from power_stash.inputs.entsoe.config import EntsoeEnv
from power_stash.inputs.entsoe.request import EntsoeRequest, RequestType
from power_stash.models.fetcher import FetcherInterface

logger = structlog.get_logger()

entsoe_env = EntsoeEnv()  # type: ignore

DEFAULT_RESOLUTION_DAY_HEAD_PRICE: str = "60T"

RETURN_NET_GENERATTION: bool = False

MAX_RETRY = 3
MAX_WAIT_PERIOD = 60


class EntsoeFetcher(FetcherInterface):
    def __init__(self) -> None:
        self.client = EntsoePandasClient(
            api_key=entsoe_env.security_token.get_secret_value(),
        )

    def _fetch_installed_capacity(
        self,
        area: Area,
        start: pd.Timestamp,
        end: pd.Timestamp,
        psr_type: str | None = None,
    ) -> pd.DataFrame:
        """Query installed capacity.

        Use the raw client instead as the `EntsoePandasClient` seems to drop data when trucating
        frames inside the `year_limited` wrapper.
        """
        blocks = year_blocks(start=start, end=end)
        all_blocks_df = []
        for _start, _end in blocks:
            text = super(EntsoePandasClient, self.client).query_installed_generation_capacity(
                country_code=area,
                start=_start,
                end=_end,
                psr_type=psr_type,
            )
            df_block = parse_generation(text)
            # Truncate to YearBegin and YearEnd, because answer is always year-based
            df_block = df_block.truncate(before=start - YearBegin(), after=end + YearEnd())
            all_blocks_df.append(df_block)

        df = pd.concat(all_blocks_df, axis=0)

        df.drop_duplicates(inplace=True)
        return df

    @retry(
        wait=wait_fixed(MAX_WAIT_PERIOD),
        stop=stop_after_attempt(MAX_RETRY),
        retry=retry_if_exception_type(HTTPError),
    )
    @retry(
        wait=wait_exponential(multiplier=1, max=MAX_WAIT_PERIOD),
        stop=stop_after_attempt(MAX_RETRY),
        retry=retry_if_exception_type(ConnectionError),
    )
    def fetch_data(self, *, request: EntsoeRequest) -> pd.DataFrame | None:  # noqa: D102
        _start = pd.to_datetime(request.start)
        _end = pd.to_datetime(request.end)
        try:
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
                    resolution = request.resolution or DEFAULT_RESOLUTION_DAY_HEAD_PRICE
                    result = self.client.query_day_ahead_prices(
                        country_code=request.area,
                        start=_start,
                        end=_end,
                        resolution=resolution,  # type: ignore (issue from the entsoe-py library ¯\_(ツ)_/¯)
                    )
                    result = pd.DataFrame(result, columns=["Day-ahead Price"])
                case RequestType.INSTALLED_GENERATION_CAPACITY:
                    # the data is yearly in this case so let's ovewrite the _start and _end to YS.
                    _start = _start.replace(month=12, day=1)
                    _end = _end.replace(month=12, day=31)
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
            result = result.tz_convert("UTC")
            # drop potential duplicates
            result.drop_duplicates(inplace=True)
        except NoMatchingDataError:
            # the specified area does not have any results
            logger.debug(
                event="fetch_data did not find matching data for request!",
                request=request,
            )
            result = None
        except HTTPError as e:
            # the specified area does not have any results if bad request returned
            if "Bad Request for url" not in str(e):
                raise e
            result = None

        return result
