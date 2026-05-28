from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    debug: bool = False

    model_config = {"env_prefix": "QTCLOUD_HR_"}
