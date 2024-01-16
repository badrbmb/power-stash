import datetime as dt
from enum import Enum

import structlog
import typer
from typing_extensions import Annotated

from power_stash.models.fetcher import FetcherInterface
from power_stash.models.processor import BaseProcessor
from power_stash.models.request import BaseRequestBuilder
from power_stash.models.storage.database import DatabaseRepository
from power_stash.services.service import PowerConsumerService

logger = structlog.getLogger()
app = typer.Typer()

DEFAULT_DATETIME_FORMATS = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S%z"]


class DataSource(str, Enum):
    ENTSOE = "entsoe"


class RepositoryType(str, Enum):
    DATABASE = "database"


def parse_datetime(datetime_str: str) -> dt.datetime:
    """Convert dates to datetime objects."""
    for fmt in DEFAULT_DATETIME_FORMATS:
        try:
            result = dt.datetime.strptime(datetime_str, fmt)
            if result.tzinfo is None:
                result = result.replace(tzinfo=dt.timezone.utc)
                logger.debug(
                    event="Missing timezone, assuming UTC.",
                    raw=datetime_str,
                    parsed=result,
                )
            return result
        except ValueError:
            continue
    raise ValueError(f"No valid format found for date: {datetime_str}")


def load_source(source: DataSource) -> tuple[BaseRequestBuilder, FetcherInterface, BaseProcessor]:
    """Load all ressources associated with the chosen data source."""
    match source:
        case DataSource.ENTSOE:
            from power_stash.inputs.entsoe.fetcher import EntsoeFetcher
            from power_stash.inputs.entsoe.processor import EntsoeProcessor
            from power_stash.inputs.entsoe.request import EntsoeRequestBuilder

            request_builder = EntsoeRequestBuilder()
            fetcher = EntsoeFetcher()
            processor = EntsoeProcessor()
        case _:
            raise NotImplementedError(f"{source=} not implemented!")

    return request_builder, fetcher, processor


def load_repository(repository_type: RepositoryType) -> DatabaseRepository:
    """Load the repository."""
    match repository_type:
        case RepositoryType.DATABASE:
            from power_stash.outputs.database.repository import SqlRepository

            repository = SqlRepository()
        case _:
            raise NotImplementedError(f"{repository_type=} not implemented!")

    return repository


@app.command()
def download_data(
    start: Annotated[
        str,
        typer.Option(
            ...,
            formats=DEFAULT_DATETIME_FORMATS,
            help="the start date for data downloading.",
        ),
    ],
    end: Annotated[
        str,
        typer.Option(
            ...,
            formats=DEFAULT_DATETIME_FORMATS,
            help="the end date for data downloading.",
        ),
    ],
    source: Annotated[
        DataSource,
        typer.Option(..., help="the source to download electricity data from."),
    ],
    repository_type: Annotated[
        RepositoryType,
        typer.Option(help="the repository handling the storage of processed data."),
    ],
) -> None:
    """CLI method to download datasets."""
    # parse datetime strs
    start_timestamp = parse_datetime(start)
    end_timestamp = parse_datetime(end)

    # load the ressources
    request_builder, fetcher, processor = load_source(source)

    repository = load_repository(repository_type)

    service = PowerConsumerService(
        request_builder=request_builder,
        fetcher=fetcher,
        processor=processor,
        repository=repository,
    )

    service.download_data(
        start=start_timestamp,
        end=end_timestamp,
    )


if __name__ == "__main__":
    app()
