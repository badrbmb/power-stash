from abc import ABC, abstractmethod

import pandas as pd

from power_stash.models.request import BaseRequest
from power_stash.models.storage.database import BaseTableModel


class BaseProcessor(ABC):
    @abstractmethod
    def transform(
        self,
        *,
        df_raw: pd.DataFrame,
        request: BaseRequest,
    ) -> list[BaseTableModel]:
        """Process a raw DataFrame."""
        pass
