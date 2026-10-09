import pytest

from config.config import settings
from smi.integration import abcex


@pytest.fixture
def abcex_api(monkeypatch, market_factory):
    market = market_factory("abcex")
    payloads = {
        "assets": [
            {"assetId": "usdt-id", "code": "USDT"},
            {"assetId": "rub-id", "code": "RUB"},
            {"assetId": "usd-id", "code": "USD"},
            {"assetId": "btc-id", "code": "BTC"},
        ],
        "instruments": [
            {"baseAssetId": "usdt-id", "quotedAssetId": "rub-id", "isActive": True, "isListed": True},
            {"baseAssetId": "usdt-id", "quotedAssetId": "usd-id", "isActive": False, "isListed": True},
            {"baseAssetId": "btc-id", "quotedAssetId": "usdt-id", "isActive": True, "isListed": False},
        ],
        "tickers": {
            "tickers": [
                {"symbol": "USDTRUB", "lastPrice": "100", "askPrice": "101", "bidPrice": "99"},
                {"symbol": "USDTUSD", "lastPrice": "2"},
                {"symbol": "BTCUSDT", "lastPrice": "50000"},
                {"symbol": "USDTRUBN", "lastPrice": "101"},
            ]
        },
    }
    endpoints = {
        market.info_url.unicode_string(): "instruments",
        settings.abcex_assets_url.unicode_string(): "assets",
        market.rates_url.unicode_string(): "tickers",
    }

    async def fake_fetch_data(url, *args, **kwargs):
        return payloads[endpoints[url]]

    monkeypatch.setattr(abcex, "fetch_data", fake_fetch_data)
    return market, payloads


def test_abcex_returns_last_price_and_reverse_rate_for_active_pairs(
    abcex_api, run_async, rates_by_symbol,
):
    market, _ = abcex_api

    symbols = run_async(abcex.fetch_abcex_symbols(market))
    rates = run_async(abcex.fetch_abcex_rates(market))

    assert [symbol.symbol for symbol in symbols] == ["USDTRUB"]
    assert {symbol.symbol for symbol in market.symbols} == {"USDTRUB", "RUBUSDT"}
    by_symbol = rates_by_symbol(rates)
    assert set(by_symbol) == {"USDTRUB", "RUBUSDT"}
    assert by_symbol["USDTRUB"].stock_market == "Abcex"
    assert by_symbol["USDTRUB"].course == pytest.approx(100)
    assert by_symbol["RUBUSDT"].course == pytest.approx(0.01)
    assert by_symbol["USDTRUB"].calculated is False
    assert by_symbol["RUBUSDT"].calculated is True
    assert by_symbol["USDTRUB"].updated == by_symbol["RUBUSDT"].updated


@pytest.mark.parametrize("endpoint,payload", [
    ("instruments", []),
    ("instruments", {}),
    ("assets", []),
    ("assets", {}),
    ("tickers", {}),
    ("tickers", {"tickers": []}),
])
def test_abcex_returns_empty_result_for_empty_response(abcex_api, run_async, endpoint, payload):
    market, payloads = abcex_api
    payloads[endpoint] = payload
    fetch = abcex.fetch_abcex_rates if endpoint == "tickers" else abcex.fetch_abcex_symbols

    result = run_async(fetch(market))

    assert result == []
    assert market.symbols == []
