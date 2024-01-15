from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    host: str = Field(alias="postgres_host")
    port: int = Field(alias="postgres_port")
    db_name: str = Field(alias="postgres_db")
    user: str = Field(alias="postgres_user")
    password: SecretStr = Field(alias="postgres_password")

    @property
    def connection(self) -> str:
        """Database url."""
        return PostgresDsn.build(
            scheme="postgresql",
            username=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            path=self.db_name,
        ).unicode_string()
