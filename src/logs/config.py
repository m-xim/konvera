from enum import StrEnum, auto

from pydantic import BaseModel, field_validator


class LogRenderer(StrEnum):
    JSON = auto()
    CONSOLE = auto()


class LogConfig(BaseModel):
    show_datetime: bool
    datetime_format: str
    show_debug_logs: bool
    time_in_utc: bool
    use_colors_in_console: bool
    renderer: LogRenderer
    allow_third_party_logs: bool

    @classmethod
    @field_validator("renderer", mode="before")
    def log_renderer_to_lower(cls, v: str):
        return v.lower()
