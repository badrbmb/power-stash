from abc import ABC, abstractmethod

import pandas as pd


class BaseProcessor(ABC):
    @abstractmethod
    def transform(
        self,
        *,
        df_raw: pd.DataFrame,
    ) -> pd.DataFrame:
        """Process a raw DataFrame."""
        pass
