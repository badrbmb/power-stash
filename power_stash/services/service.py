import datetime as dt
import time
from typing import Callable

import pandas as pd
import structlog
from dask.bag.core import Bag, from_sequence

from power_stash.models.fetcher import FetcherInterface
from power_stash.models.processor import BaseProcessor
from power_stash.models.request import BaseRequest, BaseRequestBuilder
from power_stash.models.storage.database import BaseTableModel, DatabaseRepository

logger = structlog.get_logger()


class PowerConsumerService:
    """Service class for the power data consumer."""

    def __init__(
        self,
        *,
        request_builder: BaseRequestBuilder,
        fetcher: FetcherInterface,
        processor: BaseProcessor,
        repository_factory: Callable,
    ) -> None:
        self.request_builder = request_builder
        self.fetcher = fetcher
        self.processor = processor
        self.repository_factory = repository_factory

    def _build_default_requests(
        self,
        start: dt.datetime,
        end: dt.datetime,
    ) -> list[BaseRequest]:
        return self.request_builder.build_default_requests(
            start=start,
            end=end,
        )

    def _create_repository(self) -> DatabaseRepository:
        return self.repository_factory()

    def _download(self, request: BaseRequest) -> tuple[pd.DataFrame | None, BaseRequest]:
        df_raw = self.fetcher.fecth_data(request=request)
        return df_raw, request

    def _transform(self, df_raw_request: tuple[pd.DataFrame, BaseRequest]) -> list[BaseTableModel]:
        df_raw, request = df_raw_request
        return self.processor.transform(df_raw=df_raw, request=request)

    def _add_to_repository(self, records: list[BaseTableModel]) -> None:
        """Helper function to filter out existing records and add new one."""
        repository = self._create_repository()
        repository.bulk_add(records=records)

    def _build_dask_pipeline(self, all_requests: list[BaseRequest]) -> Bag:
        dask_bag = (
            from_sequence(all_requests)
            .map(self._download)
            # filter out failed downloads
            .filter(lambda x: x[0] is not None)
            .map(self._transform)
            # store in repository
            .map(self._add_to_repository)
        )
        return dask_bag

    def download_data(
        self,
        start: dt.datetime,
        end: dt.datetime,
        scheduler: str | None = None,
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
            count_requests=len(all_requests),
        )
        pipeline = self._build_dask_pipeline(all_requests)
        pipeline.compute(scheduler=scheduler)

        end_time = time.perf_counter()
        logger.info(
            event="Download datasets: END",
            elapsed_time_secs=end_time - start_time,
        )
