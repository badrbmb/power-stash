from pandas import DataFrame

from power_stash.inputs.entsoe import models
from power_stash.inputs.entsoe.request import EntsoeRequest, RequestType
from power_stash.models.processor import BaseProcessor
from power_stash.models.storage.database import BaseTableModel


class EntsoeProcessor(BaseProcessor):
    def transform(self, *, df_raw: DataFrame, request: EntsoeRequest) -> list[BaseTableModel]:
        """Transform raw DataFrame to parsed model."""
        match request.request_type:
            case RequestType.CONSUMPTION:
                base_model = models.EntsoeConsumption
            case RequestType.GENERATION:
                raise NotImplementedError
            case RequestType.DAY_AHEAD_PRICE:
                raise NotImplementedError
            case RequestType.INSTALLED_GENERATION_CAPACITY:
                raise NotImplementedError
            case _:
                raise NotImplementedError(
                    f"fetch_data for request_type={request.request_type} not implemented!",
                )

        return df_raw.apply(
            lambda x: base_model.from_raw_record(data=x, area=request.area),
            axis=1,
        ).values.tolist()
