from dynaconf import Dynaconf
from pydantic import BaseModel

from src.logs.config import LogConfig
from src.utils.resource_path import resource_path


class Main(BaseModel):
    title: str


class Config(BaseModel):
    main: Main
    logging: LogConfig

    class Config:
        alias_generator = str.upper
        extras = "allow"


def parse_config():
    settings = Dynaconf(envvar_prefix=False, settings_files=[resource_path("settings.toml")], load_dotenv=False)
    return Config.model_validate(settings.as_dict())


config = parse_config()
