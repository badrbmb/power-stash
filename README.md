# power-stash

Python package to fetch, process and store electricity data from different providers.

##  Overview

`power-stash` is a python package designed to fecth electricity data (consumption, generation, exchange, prices, ...) from various sources, process them leveraging dask and pandas and store the resulting timeseries in a Timescale database.

The project is structured following an (attempt of) hexagonal architecture pattern, with the core functionality of the project housed under power_stash/services, interfaces defined under power_stash/models and i/o and external actors defined under power_stash/inputs and power_stash/outputs respectively.

Inputs from data providers currently implemented under power_stash/inputs are from ENSTOE, covering both hourly consumption, production, day ahead prices and exhanges accross all zones available.

---

##  Repository Structure

```sh
└── power-stash/
    ├── .env.sample
    ├── docker-compose.yml
    ├── power_stash
    │   ├── config.py
    │   ├── constants.py
    │   ├── inputs
    │   │   └── entsoe
    │   ├── main.py
    │   ├── models
    │   │   ├── fetcher.py
    │   │   ├── processor.py
    │   │   ├── request.py
    │   │   └── storage
    │   ├── outputs
    │   │   ├── database
    │   │   └── localfs
    │   ├── services
    │   │   └── service.py
    │   └── utils.py
    └── pyproject.toml
```

---

##  Modules

<details closed><summary>power_stash</summary>

| File                                                                                        | Summary                                                                                                                                                                                                                             |
| ---                                                                                         | ---                                                                                                                                                                                                                                 |
| [main.py](https://github.com/badrbmb/power-stash/blob/master/power_stash/main.py)           | This code enables data extraction, processing, and storage from specified electricity data sources, utilizing a configurable Dask cluster for parallel processing and a CLI for user interaction within the service's architecture. |

</details>

<details closed><summary>power_stash.models</summary>

| File                                                                                               | Summary                                                                                                                                                                                                                   |
| ---                                                                                                | ---                                                                                                                                                                                                                       |
| [request.py](https://github.com/badrbmb/power-stash/blob/master/power_stash/models/request.py)     | Defines an abstract request model and builder for time-bounded data fetching tasks, including validation and status tracking.                                                                                             |
| [processor.py](https://github.com/badrbmb/power-stash/blob/master/power_stash/models/processor.py) | The `processor.py` defines an abstract base class for transforming raw data into a format suitable for database storage.                                                                                                  |
| [fetcher.py](https://github.com/badrbmb/power-stash/blob/master/power_stash/models/fetcher.py)     | The `fetcher.py` defines an interface for fetching electricity data, integrating with external sources to supply data in a DataFrame, crucial for the modularity in data retrieval within the `power-stash` architecture. |

</details>

<details closed><summary>power_stash.services</summary>

| File                                                                                             | Summary                                                                                                                                                                            |
| ---                                                                                              | ---                                                                                                                                                                                |
| [service.py](https://github.com/badrbmb/power-stash/blob/master/power_stash/services/service.py) | The `PowerConsumerService` in `service.py` orchestrates data flow: fetching, processing, storage, and error-handling, for power data within a parallelized, dask-powered pipeline. |

</details>

<details closed><summary>power_stash.models.storage</summary>

| File                                                                                                     | Summary                                                                                                                                                        |
| ---                                                                                                      | ---                                                                                                                                                            |
| [database.py](https://github.com/badrbmb/power-stash/blob/master/power_stash/models/storage/database.py) | Defines database models and repository interface for managing power data within parent architecture; represents requests and abstracts persistence operations. |
| [blob.py](https://github.com/badrbmb/power-stash/blob/master/power_stash/models/storage/blob.py)         | The `blob.py` defines a storage interface for managing data blobs, crucial for the archiving functionality within the `power-stash` repository.                |

</details>

<details closed><summary>power_stash.outputs.database</summary>

| File                                                                                                           | Summary                                                                                                                                                                                                                                                         |
| ---                                                                                                            | ---                                                                                                                                                                                                                                                             |
| [config.py](https://github.com/badrbmb/power-stash/blob/master/power_stash/outputs/database/config.py)         | The snippet defines database settings for a Postgres instance within `power-stash` architecture, handling secure credential storage and connection string construction.                                                                                         |
| [tables.py](https://github.com/badrbmb/power-stash/blob/master/power_stash/outputs/database/tables.py)         | Defines database hypertables, integrating energy data models with the repository's data storage architecture.                                                                                                                                                   |
| [repository.py](https://github.com/badrbmb/power-stash/blob/master/power_stash/outputs/database/repository.py) | The `SqlRepository` class manages database operations, providing methods to initialize the database with TimeScale hypertables, check existence, add, update, and bulk insert records, and execute queries within the `power-stash` energy data infrastructure. |

</details>

<details closed><summary>power_stash.outputs.localfs</summary>

| File                                                                                                            | Summary                                                                                                                                                                     |
| ---                                                                                                             | ---                                                                                                                                                                         |
| [blob_client.py](https://github.com/badrbmb/power-stash/blob/master/power_stash/outputs/localfs/blob_client.py) | LocalClient in power_stash manages file storage, ensuring file existence, validating size, listing, storing datasets as Parquet, and deleting files or directories locally. |

</details>

<details closed><summary>power_stash.inputs.entsoe</summary>

| File                                                                                                      | Summary                                                                                                                                                                                                |
| ---                                                                                                       | ---                                                                                                                                                                                                    |
| [config.py](https://github.com/badrbmb/power-stash/blob/master/power_stash/inputs/entsoe/config.py)       | The `config.py` within `power_stash/inputs/entsoe` manages configuration, securely handling the ENTSO-E API token for data retrieval in the energy data platform's architecture.                       |
| [models.py](https://github.com/badrbmb/power-stash/blob/master/power_stash/inputs/entsoe/models.py)       | Models define energy data structure, parse raw records, and compute unique IDs for database integration within the energy data management system.                                                      |
| [request.py](https://github.com/badrbmb/power-stash/blob/master/power_stash/inputs/entsoe/request.py)     | The `request.py` module defines `EntsoeRequest` classes for querying power data by area and type, and builds default batch requests within the data ingestion pipeline of the Power Stash application. |
| [processor.py](https://github.com/badrbmb/power-stash/blob/master/power_stash/inputs/entsoe/processor.py) | EntsoeProcessor transforms ENTSO-E data, fitting it to database models for various request types within power data management system.                                                                  |
| [fetcher.py](https://github.com/badrbmb/power-stash/blob/master/power_stash/inputs/entsoe/fetcher.py)     | This `fetcher.py` within `power-stash` handles data retrieval from the ENTSO-E API, with retries for resilience, and provides electricity market data like load, generation, prices, and capacity.     |

</details>

---

##  Getting Started

Make sure you're ideally working on a new virtual env with Poetry installed. Install the dependencies with:

```poetry install```

###  Running power-stash

If you're using vs code, you might find some usefull launch scripts in .vscode/launch.json, otherwise feel free to have a look at power_stash/main.py help running:

```sh
python power_stash/main.py --help
```

Make sure you have a running instance of the TimescaleDB (to store the downloaded time-series). There's a docker-compose file to help with that, refer to `docker-compose.yml` for more details, or run the following command:

```sh
docker-compose up
```

###  Tests

To execute tests, run:

```sh
pytest
```

---

##  Acknowledgments

TODO