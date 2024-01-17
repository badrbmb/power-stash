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
        data = data.where(pd.notna(data), None)

        timestamp: pd.Timestamp = data["timestamp"]
        return cls(
            timestamp=timestamp.to_pydatetime(),
            value=data["Actual Load"],
            unit="MW",
            area=area,
        )


class EntsoeGeneration(BaseTableModel, table=True):
    timestamp: dt.datetime = Field(primary_key=True)
    aggregated_value: float | None
    consumption_value: float | None
    unit: str
    area: Area
    resource: str
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
        uid_params = f"{self.resource}_{self.area}_{self.timestamp}"
        return hashlib.sha1(uid_params.encode("utf-8")).hexdigest()  # noqa: S324

    @classmethod
    def from_raw_record(cls, data: pd.Series, area: Area) -> "EntsoeGeneration":  # noqa: ANN102
        """Parse pd.Series into a new model."""
        data = data.where(pd.notna(data), None)

        timestamp: pd.Timestamp = data["timestamp"]
        return cls(
            timestamp=timestamp.to_pydatetime(),
            aggregated_value=data["Actual Aggregated"],
            consumption_value=data["Actual Consumption"],
            unit="MW",
            area=area,
            resource=data["resource"],
        )


class EntsoeDayAheadPrice(BaseTableModel, table=True):
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
    def from_raw_record(cls, data: pd.Series, area: Area) -> "EntsoeDayAheadPrice":  # noqa: ANN102
        """Parse pd.Series into a new model."""
        data = data.where(pd.notna(data), None)

        timestamp: pd.Timestamp = data["timestamp"]
        return cls(
            timestamp=timestamp.to_pydatetime(),
            value=data["Day-ahead Price"],
            unit="EUR / MWh",
            area=area,
        )
