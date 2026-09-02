import pytest

from smi.integration import binance_p2p, bybit_p2p
from smi.schemas import Symbol


def test_binance_p2p_symbols_are_static_direct_pairs(run_async, market_factory):
    market = market_factory("binance_p2p")

    symbols = run_async(binance_p2p.fetch_binance_p2p_symbols(market))

    assert {symbol.symbol for symbol in symbols} == {"USDTKZT", "USDTTJS", "USDTAZN", "USDTARS"}
    assert {symbol.symbol for symbol in market.symbols} == {"USDTKZT", "USDTTJS", "USDTAZN", "USDTARS"}


def test_bybit_p2p_symbols_include_reverse_pairs(run_async, market_factory):
    market = market_factory("bybit_p2p")

    symbols = run_async(bybit_p2p.fetch_bybit_p2p_symbols(market))

    assert {symbol.symbol for symbol in symbols} == {"USDTRUB", "USDTKZT", "USDTAZN", "USDTTJS", "USDTARS", "USDTEGP"}
    assert "AZNUSDT" in {symbol.symbol for symbol in market.symbols}
    assert "USDTAZN" in {symbol.symbol for symbol in market.symbols}
    assert "EGPUSDT" in {symbol.symbol for symbol in market.symbols}


P2P_RATE_CASES = [
    (
        "binance_p2p",
        binance_p2p,
        binance_p2p.fetch_binance_p2p_rates,
        "BUY",
        "SELL",
        {"min_amount": 0, "verify": True, "bank": []},
    ),
    (
        "bybit_p2p",
        bybit_p2p,
        bybit_p2p.fetch_bybit_p2p_rates,
        "1",
        "0",
        {"min_amount": 0, "merchant_only": True, "payment": []},
    ),
]


@pytest.mark.parametrize(
    "settings_attr, module, fetch_rates, buy_side, sell_side, expected_default_kwargs",
    P2P_RATE_CASES,
    ids=[case[0] for case in P2P_RATE_CASES],
)
def test_p2p_rates_use_default_window_and_return_direct_and_reverse_rates(
    monkeypatch,
    run_async,
    market_factory,
    rates_by_symbol,
    settings_attr,
    module,
    fetch_rates,
    buy_side,
    sell_side,
    expected_default_kwargs,
):
    market = market_factory(settings_attr)
    market.symbols = [Symbol(asset_left="USDT", asset_right="KZT")]
    seen_calls = []

    async def fake_fetch_ads(market_arg, symbol_arg, side, *args, **kwargs):
        seen_calls.append((market_arg, symbol_arg, side, kwargs))
        if side == buy_side:
            return [10.0, 20.0, 30.0, 40.0, 50.0]
        if side == sell_side:
            return [100.0, 90.0, 80.0, 70.0, 60.0]
        return []

    monkeypatch.setattr(module, "fetch_ads", fake_fetch_ads)

    rates = run_async(fetch_rates(market))

    by_symbol = rates_by_symbol(rates)
    assert set(by_symbol) == {"USDTKZT", "KZTUSDT"}
    assert by_symbol["USDTKZT"].course == pytest.approx(80.0)
    assert by_symbol["KZTUSDT"].course == pytest.approx(1 / 30.0)
    assert [call[2] for call in seen_calls] == [buy_side, sell_side]
    for market_arg, symbol_arg, side, kwargs in seen_calls:
        assert market_arg is market
        assert symbol_arg.symbol == "USDTKZT"
        for key, value in expected_default_kwargs.items():
            assert kwargs[key] == value


def test_binance_p2p_fetch_ads_parses_and_sorts_prices(monkeypatch, run_async, market_factory):
    captured_payloads = []

    async def fake_fetch_data(url, *, json=None, **kwargs):
        captured_payloads.append(json)
        return {
            "data": [
                {"adv": {"price": "10.0"}},
                {"adv": {"price": "8.0"}},
                {"adv": {"price": None}},
                {},
            ]
        }

    monkeypatch.setattr(binance_p2p, "fetch_data", fake_fetch_data)
    market = market_factory("binance_p2p")
    symbol = Symbol(asset_left="USDT", asset_right="KZT")

    buy_prices = run_async(binance_p2p.fetch_ads(market, symbol, "BUY", rows=20))
    sell_prices = run_async(binance_p2p.fetch_ads(market, symbol, "SELL", rows=20))

    assert buy_prices == [8.0, 10.0]
    assert sell_prices == [10.0, 8.0]
    assert captured_payloads[0]["asset"] == "USDT"
    assert captured_payloads[0]["fiat"] == "KZT"
    assert captured_payloads[0]["tradeType"] == "BUY"
    assert captured_payloads[0]["merchantCheck"] is True


def test_bybit_p2p_fetch_ads_filters_verified_merchants(monkeypatch, run_async, market_factory):
    captured_payloads = []

    async def fake_fetch_data(url, *, json=None, **kwargs):
        captured_payloads.append(json)
        return {
            "result": {
                "items": [
                    {"price": "10.0", "authTag": ["VA"]},
                    {"price": "8.0", "authTag": []},
                    {"price": "bad", "authTag": ["VA"]},
                ]
            }
        }

    monkeypatch.setattr(bybit_p2p, "fetch_data", fake_fetch_data)
    market = market_factory("bybit_p2p")
    symbol = Symbol(asset_left="USDT", asset_right="KZT")

    prices = run_async(bybit_p2p.fetch_ads(market, symbol, "1", min_amount=1000, payment=["169"]))

    assert prices == [10.0]
    assert captured_payloads[0]["tokenId"] == "USDT"
    assert captured_payloads[0]["currencyId"] == "KZT"
    assert captured_payloads[0]["side"] == "1"
    assert captured_payloads[0]["amount"] == "1000"
    assert captured_payloads[0]["payment"] == ["169"]


def test_bybit_p2p_egp_uses_vodafone_cash_window(monkeypatch, run_async, market_factory):
    seen_calls = []

    async def fake_fetch_ads(market_arg, symbol_arg, side, *args, **kwargs):
        seen_calls.append((side, kwargs))
        if side == "1":
            return [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        return [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0]

    monkeypatch.setattr(bybit_p2p, "fetch_ads", fake_fetch_ads)
    market = market_factory("bybit_p2p")
    symbol = Symbol(asset_left="USDT", asset_right="EGP")

    result = run_async(bybit_p2p.compute_pair_avg(market, symbol))

    assert result == {"symbol": "USDTEGP", "price": (6.0, 5.0)}
    assert [side for side, _ in seen_calls] == ["1", "0"]
    for _, kwargs in seen_calls:
        assert kwargs == {"min_amount": 1000, "merchant_only": True, "payment": ["169"]}
