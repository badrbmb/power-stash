import datetime as dt
import hashlib

import pandas as pd
from sqlmodel import Field

from power_stash.inputs.entsoe.request import Area
from power_stash.models.storage.database import BaseTableModel


class EntsoeConsumption(BaseTableModel, table=True):
    timestamp: dt.datetime = Field(primary_key=True)
    value: float
    unit: str
    area: Area
    last_updated: dt.datetime = Field(default=dt.datetime.now(tz=dt.timezone.utc))

    def __init__(
        self,
        **data,  # noqa: ANN003
    ) -> None:
        super().__init__(**data)
        # override uid property
        self.uid = self.compute_uid()

    def compute_uid(self) -> str:
        """Unique identifier based on fields."""
        uid_params = f"{self.area}_{self.timestamp}"
        return hashlib.sha1(uid_params.encode("utf-8")).hexdigest()  # noqa: S324

    @classmethod
    def from_raw_record(cls, data: pd.Series, area: Area) -> "EntsoeConsumption":  # noqa: ANN102
        """Parse pd.Series into a new model."""
        timestamp: pd.Timestamp = data.name
        return EntsoeConsumption(
            timestamp=timestamp.to_pydatetime(),
            value=data["Actual Load"],
            unit="MW",
            area=area,
        )
