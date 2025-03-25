from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import Any
from datetime import datetime


class Asset(BaseModel):
    asset: str

    @field_validator('asset', mode='before')
    def convert_to_uppercase(cls, v: Any) -> str:
        if type(v) == Asset:
            return v.asset.upper()
        return v.upper()


class Symbol(BaseModel):
    asset_left: Asset
    asset_right: Asset
    symbol: str = Field(default=None, init=False)

    @field_validator('asset_left', 'asset_right', mode='before')
    def ensure_assets(cls, v: Any) -> Asset:
        return Asset(asset=v)

    def __init__(self, **data: Any):
        super().__init__(**data)
        if self.symbol is None:
            self.symbol = f"{self.asset_left.asset}{self.asset_right.asset}"


class StockMarket(BaseModel):
    name: str
    info_url: HttpUrl
    rates_url: HttpUrl
    requests_sleep: int
    requests_per_day: int
    symbols: list[Symbol] = []  # Список используемых символов


class SMCourse(BaseModel):
    stock_market: str
    symbol: str # Symbol
    course: float
    calculated: bool
    updated: datetime
