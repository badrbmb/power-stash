import pandas as pd

from power_stash.inputs.entsoe import models
from power_stash.inputs.entsoe.request import EntsoeRequest, RequestType
from power_stash.models.processor import BaseProcessor
from power_stash.models.storage.database import BaseTableModel


class EntsoeProcessor(BaseProcessor):
    def transform(self, *, df_raw: pd.DataFrame, request: EntsoeRequest) -> list[BaseTableModel]:
        """Transform raw DataFrame to parsed model."""
        df = df_raw.copy()
        df.index.name = "timestamp"
        df.reset_index(inplace=True)
        match request.request_type:
            case RequestType.CONSUMPTION:
                base_model = models.EntsoeHourlyConsumption
            case RequestType.GENERATION:
                # melt multi-index columns
                df = df.melt(
                    id_vars=["timestamp"],
                    var_name=["resource", "type"],
                    value_name="value",
                )
                # pivot by type
                df = df.pivot(
                    index=["timestamp", "resource"],
                    columns="type",
                    values="value",
                ).reset_index()
                base_model = models.EntsoeHourlyGeneration
            case RequestType.DAY_AHEAD_PRICE:
                base_model = models.EntsoeHourlyDayAheadPrice
            case RequestType.INSTALLED_GENERATION_CAPACITY:
                # melt columns
                df = df.melt(
                    id_vars="timestamp",
                    value_name="Installed Capacity",
                    var_name="resource",
                )
                base_model = models.EntsoeYearlyInstalledCapacity
            case _:
                raise NotImplementedError(
                    f"fetch_data for request_type={request.request_type} not implemented!",
                )

        records = df.apply(
            lambda x: base_model.from_raw_record(data=x, area=request.area),
            axis=1,
        ).tolist()

        del df

        return records
