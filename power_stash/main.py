import datetime as dt
from enum import Enum
from typing import Callable

import structlog
import typer
from distributed import Client, SpecCluster
from typing_extensions import Annotated

from power_stash.models.fetcher import FetcherInterface
from power_stash.models.processor import BaseProcessor
from power_stash.models.request import BaseRequestBuilder
from power_stash.outputs.database.repository import DatabaseRepository
from power_stash.services.service import PowerConsumerService

logger = structlog.getLogger()
app = typer.Typer()

DEFAULT_DATETIME_FORMATS = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S%z"]

DEFAULT_WORKER_NUMBER = 1

DEFAULT_THREADS_BY_WORKER = 5


class DataSource(str, Enum):
    ENTSOE = "entsoe"


class RepositoryType(str, Enum):
    DATABASE = "database"


class ClusterType(str, Enum):
    LOCAL = "local"


def parse_datetime(datetime_str: str) -> dt.datetime:
    """Convert dates to datetime objects."""
    for fmt in DEFAULT_DATETIME_FORMATS:
        try:
            result = dt.datetime.strptime(datetime_str, fmt)  # noqa: DTZ007
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


def load_repository_factory(repository_type: RepositoryType) -> Callable:
    """Load a callable to repository when required."""

    def _create_sql_repository() -> DatabaseRepository:
        from power_stash.outputs.database.repository import SqlRepository

        return SqlRepository()

    match repository_type:
        case RepositoryType.DATABASE:
            return _create_sql_repository
        case _:
            raise NotImplementedError(f"{repository_type=} not implemented!")


def load_cluster(
    cluster_type: ClusterType,
    n_workers: int,
    threads_per_worker: int,
    name: str = "Power Stash data download cluster.",
) -> SpecCluster:
    """Load cluster."""
    match cluster_type:
        case ClusterType.LOCAL:
            from distributed import LocalCluster

            cluster = LocalCluster(
                name=name,
                n_workers=n_workers,
                threads_per_worker=threads_per_worker,
            )
        case _:
            raise NotImplementedError(f"{cluster_type=} not implemented yet!")

    return cluster


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
    cluster_type: Annotated[
        ClusterType,
        typer.Option(help="the type of cluster."),
    ] = ClusterType.LOCAL,
    n_workers: Annotated[
        int,
        typer.Option(help="the number of workers in dask cluster."),
    ] = DEFAULT_WORKER_NUMBER,
    threads_per_worker: Annotated[
        int,
        typer.Option(help="the number of threads per worker in the cluster."),
    ] = DEFAULT_THREADS_BY_WORKER,
) -> None:
    """CLI method to download datasets."""
    # parse datetime strs
    start_timestamp = parse_datetime(start)
    end_timestamp = parse_datetime(end)

    # load the ressources
    request_builder, fetcher, processor = load_source(source)

    repository_factory = load_repository_factory(repository_type)

    service = PowerConsumerService(
        request_builder=request_builder,
        fetcher=fetcher,
        processor=processor,
        repository_factory=repository_factory,
    )

    cluster = load_cluster(
        cluster_type=cluster_type,
        n_workers=n_workers,
        threads_per_worker=threads_per_worker,
    )

    # start a local dask cluster
    dask_client = Client(cluster)

    logger.info(
        event="Dask cluster started.",
        url=dask_client.dashboard_link,
        n_workers=n_workers,
        threads_per_worker=threads_per_worker,
    )

    try:
        service.download_data(
            start=start_timestamp,
            end=end_timestamp,
            # set to None when running default scheduler, or "synchronous" if override to debug
            # more info: https://docs.dask.org/en/stable/scheduling.html
            scheduler=None,
        )
    except Exception as e:
        raise e
    finally:
        # close the dask client
        dask_client.close()
        logger.debug(
            event="Dask cluster closed.",
        )


if __name__ == "__main__":
    app()
