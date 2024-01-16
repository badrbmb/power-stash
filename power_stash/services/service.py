import datetime as dt
import time

import structlog

from power_stash.models.fetcher import FetcherInterface
from power_stash.models.processor import BaseProcessor
from power_stash.models.request import BaseRequest, BaseRequestBuilder
from power_stash.models.storage.database import DatabaseRepository

logger = structlog.get_logger()


class PowerConsumerService:
    """Service class for the power data consumer."""

    def __init__(
        self,
        *,
        request_builder: BaseRequestBuilder,
        fetcher: FetcherInterface,
        processor: BaseProcessor,
        repository: DatabaseRepository,
    ) -> None:
        self.request_builder = request_builder
        self.fetcher = fetcher
        self.processor = processor
        self.repository = repository

    def _build_default_requests(
        self,
        start: dt.datetime,
        end: dt.datetime,
    ) -> list[BaseRequest]:
        return self.request_builder.build_default_requests(start=start, end=end)

    def _process_requests(
        self,
        all_requests: list[BaseRequest],
    ) -> tuple[list[BaseRequest], list[BaseRequest]]:
        successes = []
        failures = []
        for request in all_requests:
            try:
                # fetch data
                df_raw = self.fetcher.fecth_data(request=request)
                # process
                records = self.processor.transform(df_raw=df_raw, request=request)
                # store
                _ = self.repository.bulk_add(records=records)
                successes.append(request)
            except Exception as e:
                logger.error(
                    event="Processing request failed!",
                    request=request,
                    error=e,
                )
                failures.append(request)

        return successes, failures

    def download_data(
        self,
        start: dt.datetime,
        end: dt.datetime,
    ) -> None:
        """Download all power data between start and end timestamps."""
        start_time = time.perf_counter()
        logger.info(
            event="Download data: START",
            start=start,
            end=end,
        )

        all_requests = self._build_default_requests(start=start, end=end)

        logger.debug(
            event="Built requests.",
            count_all_requests=len(all_requests),
        )

        sucesses, failures = self._process_requests(all_requests)

        end_time = time.perf_counter()
        logger.info(
            event="Download datasets: END",
            count_sucess_requests=len(sucesses),
            count_failed_requests=len(failures),
            elapsed_time_secs=end_time - start_time,
        )
