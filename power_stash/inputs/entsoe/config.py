from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class EntsoeEnv(BaseSettings):
    security_token: SecretStr = Field(
        description="Web Api Security Token from the ENTSO-E platform.",
        alias="entsoe_security_token",
    )
