import datetime as dt
import time
from pathlib import Path
from typing import Callable

import pandas as pd
import structlog
from dask.bag.core import Bag, from_sequence

from power_stash.config import ERROR_DIR
from power_stash.models.fetcher import FetcherInterface
from power_stash.models.processor import BaseProcessor
from power_stash.models.request import BaseRequest, BaseRequestBuilder, RequestStatus
from power_stash.models.storage.database import (
    BaseTableModel,
    DatabaseRepository,
    RequestStatusModel,
)

logger = structlog.get_logger()

DEFAULT_MONTHLY_CHUNKS = 1


class PowerConsumerService:
    """Service class for the power data consumer."""

    def __init__(
        self,
        *,
        request_builder: BaseRequestBuilder,
        fetcher: FetcherInterface,
        processor: BaseProcessor,
        repository_factory: Callable,
        error_logs_dir: Path = ERROR_DIR,
    ) -> None:
        self.request_builder = request_builder
        self.fetcher = fetcher
        self.processor = processor
        self.repository_factory = repository_factory
        self.start_time = time.perf_counter()
        self.error_logs_dir = error_logs_dir / str(self.start_time)
        self.error_logs_dir.mkdir(exist_ok=True)

    def _build_default_requests(
        self,
        start: dt.datetime,
        end: dt.datetime,
        chunk_months: int,
    ) -> list[BaseRequest]:
        return self.request_builder.build_default_requests(
            start=start,
            end=end,
            chunk_months=chunk_months,
        )

    def _create_repository(self) -> DatabaseRepository:
        return self.repository_factory()

    def _update_registry(
        self,
        repository: DatabaseRepository,
        request: BaseRequest,
    ) -> RequestStatusModel:
        """Helper function to save status of different requets."""
        request_status = RequestStatusModel.from_request(request)
        repository.add_or_update(record=request_status)
        return request_status

    def _download(self, request: BaseRequest) -> tuple[pd.DataFrame | None, BaseRequest]:
        logger.debug(
            event="Init. download request...",
            request=request,
        )
        df_raw = self.fetcher.fecth_data(request=request)
        return df_raw, request

    def _transform(
        self,
        df_raw_request: tuple[pd.DataFrame, BaseRequest],
    ) -> tuple[list[BaseTableModel] | None, BaseRequest]:
        df_raw, request = df_raw_request
        try:
            logger.debug(
                event="Init. transform request...",
                request=request,
            )
            records = self.processor.transform(df_raw=df_raw, request=request)
        except Exception as e:
            records = None
            request.error = str(e)
            request.status = RequestStatus.FAILURE
            logger.error(
                event="Failed transforming request!",
                request=request,
                error=e,
            )
        return records, request

    def _add_to_repository(
        self,
        records_request: tuple[list[BaseTableModel] | None, BaseRequest],
    ) -> RequestStatusModel:
        """Helper function to filter out existing records and add new one."""
        records, request = records_request
        repository = self._create_repository()
        if records is not None:
            # store records in db
            repository.bulk_add(records=records)
            # update status
            request.status = RequestStatus.SUCCESS
        else:
            if request.status is None:
                request.status = RequestStatus.FAILURE
        # update registry
        request_status = self._update_registry(repository=repository, request=request)
        return request_status

    def _build_dask_pipeline(self, all_requests: list[BaseRequest]) -> Bag:
        # TODO: add option to save failed requests for debug...
        dask_bag = (
            from_sequence(all_requests)
            .map(self._download)
            # filter out failed downloads
            .filter(lambda x: x[0] is not None)
            .map(self._transform)
            # store in repository
            .map(self._add_to_repository)
            # keep only error paths
            .filter(lambda x: x is not None)
        )
        return dask_bag

    def download_data(
        self,
        start: dt.datetime,
        end: dt.datetime,
        scheduler: str | None = None,
        chunk_months: int = DEFAULT_MONTHLY_CHUNKS,
    ) -> None:
        """Download all power data between start and end timestamps."""
        logger.info(
            event="Download data: START",
            start=start,
            end=end,
            chunks=f"by {chunk_months} month(s)",
        )

        all_requests = self._build_default_requests(
            start=start,
            end=end,
            chunk_months=chunk_months,
        )

        logger.debug(
            event="Built requests.",
            count_requests=len(all_requests),
        )
        pipeline = self._build_dask_pipeline(all_requests)

        error_paths: list[Path] = pipeline.compute(scheduler=scheduler)

        if len(error_paths) > 0:
            logger.error(
                event="Failed processing requests!",
                num_failed_request=len(error_paths),
                error_logs_dir=self.error_logs_dir,
            )

        end_time = time.perf_counter()
        logger.info(
            event="Download datasets: END",
            elapsed_time_secs=end_time - self.start_time,
        )
