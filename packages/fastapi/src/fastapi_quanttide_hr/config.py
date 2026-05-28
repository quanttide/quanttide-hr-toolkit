from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./qtcloud-hr.db"
    debug: bool = True

    model_config = {"env_prefix": "QTCLOUD_HR_"}
