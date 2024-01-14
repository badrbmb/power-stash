import pandas as pd
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator


class BaseRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    start: pd.Timestamp
    end: pd.Timestamp

    @field_validator("start", "end")
    def validate_date(cls, v: pd.Timestamp) -> pd.Timestamp:
        """Validate dates of request."""
        if v.tzinfo is None:
            raise ValidationError(f"Expected a timezone info. for timestamp={v}")
        return v
