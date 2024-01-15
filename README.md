# power-stash

Python package to fetch, process and store electricity data from different providers.

# Repo structure [WIP]

.
├── .env
├── .vscode
│   ├── launch.json
│   └── settings.json
├── README.md
├── data
├── notebooks
├── poetry.lock
├── power_stash
│   ├── config.py
│   ├── constants.py
│   ├── inputs
│   │   └── entsoe
│   │       ├── config.py
│   │       ├── fetcher.py
│   │       └── request.py
│   ├── main.py
│   ├── models
│   │   ├── fetcher.py
│   │   ├── request.py
│   │   └── storage
│   │       ├── blob.py
│   │       └── timeseries.py
│   ├── outputs
│   │   └── localfs
│   │       └── blob_client.py
│   ├── services
│   │   └── service.py
│   └── utils.py
├── pyproject.toml
└── tests