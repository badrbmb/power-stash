from typing import Protocol

import pandas as pd

from power_stash.models.request import BaseRequest


class FetcherInterface(Protocol):
    """Generic interface for fetching electricity data from external sources."""

    def fetch_data(self, *, request: BaseRequest) -> pd.DataFrame:
        """Fetch the requested data and returns in a DataFrame format."""
        pass
