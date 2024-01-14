from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).parent.parent

DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


class EntsoeEnv(BaseSettings):
    security_token: SecretStr = Field(
        description="Web Api Security Token from the ENTSO-E platform.",
        alias="entsoe_security_token",
    )
