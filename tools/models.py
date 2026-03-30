from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PanelRow(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    province: str
    year: str

    @field_validator("province")
    @classmethod
    def validate_province(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("province 不能为空")
        return value

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: str) -> str:
        if not str(value).strip():
            raise ValueError("year 不能为空")
        return str(value)


class SourceRecord(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    source_level: str = Field(default="")
    source_name: str = Field(default="")
    source_url: str = Field(default="")
    source_id: str = Field(default="")
    variable: str = Field(default="")
    cross_check_url: str = Field(default="")


class SearchCandidate(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    url: str
    title: str = ""
    snippet: str = ""
    score: float = 0.0
    engine: str = ""

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("url 不能为空")
        return value


def parse_panel_row(payload: dict[str, Any]) -> PanelRow:
    return PanelRow.model_validate(payload)


def parse_source_record(payload: dict[str, Any]) -> SourceRecord:
    return SourceRecord.model_validate(payload)


def parse_search_candidate(payload: dict[str, Any]) -> SearchCandidate:
    return SearchCandidate.model_validate(payload)
