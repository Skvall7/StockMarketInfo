import asyncio
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[3]
(ROOT_DIR / "var" / "logs").mkdir(parents=True, exist_ok=True)


@pytest.fixture
def run_async():
    def runner(coro):
        return asyncio.run(coro)

    return runner


@pytest.fixture
def market_factory():
    from config.config import settings

    def create(settings_attr: str):
        market = getattr(settings, settings_attr).model_copy(deep=True)
        market.symbols = []
        return market

    return create


@pytest.fixture
def rates_by_symbol():
    def convert(rates):
        return {rate.symbol: rate for rate in rates}

    return convert
