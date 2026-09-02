import pytest

from smi.integration import binance, bybit, cbr, garantex, htx, payeer, rapira


SPOT_CASES = [
    {
        "id": "binance",
        "module": binance,
        "settings_attr": "binance",
        "fetch_symbols": binance.fetch_binance_symbols,
        "fetch_rates": binance.fetch_binance_rates,
        "symbol_payload": {
            "symbols": [
                {"baseAsset": "USDT", "quoteAsset": "RUB", "status": "TRADING"},
                {"baseAsset": "BTC", "quoteAsset": "RUB", "status": "BREAK"},
            ]
        },
        "rates_payload": [{"symbol": "USDTRUB", "price": "100.0"}],
        "empty_symbol_payload": {},
        "direct_symbol": "USDTRUB",
        "reverse_symbol": "RUBUSDT",
        "direct_course": 100.0,
    },
    {
        "id": "bybit",
        "module": bybit,
        "settings_attr": "bybit",
        "fetch_symbols": bybit.fetch_bybit_symbols,
        "fetch_rates": bybit.fetch_bybit_rates,
        "symbol_payload": {
            "result": {
                "list": [
                    {"baseCoin": "USDT", "quoteCoin": "RUB", "status": "Trading"},
                    {"baseCoin": "BTC", "quoteCoin": "RUB", "status": "Settled"},
                ]
            }
        },
        "rates_payload": {"result": {"list": [{"symbol": "USDTRUB", "lastPrice": "100.0"}]}},
        "empty_symbol_payload": {},
        "direct_symbol": "USDTRUB",
        "reverse_symbol": "RUBUSDT",
        "direct_course": 100.0,
    },
    {
        "id": "htx",
        "module": htx,
        "settings_attr": "htx",
        "fetch_symbols": htx.fetch_htx_symbols,
        "fetch_rates": htx.fetch_htx_rates,
        "symbol_payload": {
            "data": [
                {"bc": "usdt", "qc": "rub", "state": "online"},
                {"bc": "btc", "qc": "rub", "state": "offline"},
            ]
        },
        "rates_payload": {"data": [{"symbol": "usdtrub", "close": "100.0"}]},
        "empty_symbol_payload": {},
        "direct_symbol": "USDTRUB",
        "reverse_symbol": "RUBUSDT",
        "direct_course": 100.0,
    },
    {
        "id": "payeer",
        "module": payeer,
        "settings_attr": "payeer",
        "fetch_symbols": payeer.fetch_payeer_symbols,
        "fetch_rates": payeer.fetch_payeer_rates,
        "symbol_payload": {"pairs": ["USDT_RUB"]},
        "rates_payload": {"pairs": {"USDT_RUB": {"last": "100.0"}}},
        "empty_symbol_payload": {},
        "direct_symbol": "USDTRUB",
        "reverse_symbol": "RUBUSDT",
        "direct_course": 100.0,
    },
    {
        "id": "rapira",
        "module": rapira,
        "settings_attr": "rapira",
        "fetch_symbols": rapira.fetch_rapira_symbols,
        "fetch_rates": rapira.fetch_rapira_rates,
        "symbol_payload": [
            {"coinSymbol": "USDT", "baseSymbol": "RUB", "exchangeable": True},
            {"coinSymbol": "BTC", "baseSymbol": "RUB", "exchangeable": False},
        ],
        "rates_payload": {"data": [{"symbol": "USDT/RUB", "close": "100.0"}]},
        "empty_symbol_payload": [],
        "direct_symbol": "USDTRUB",
        "reverse_symbol": "RUBUSDT",
        "direct_course": 100.0,
    },
    {
        "id": "cbr",
        "module": cbr,
        "settings_attr": "cbr",
        "fetch_symbols": cbr.fetch_cbr_symbols,
        "fetch_rates": cbr.fetch_cbr_rates,
        "symbol_payload": {"Valute": {"USD": {"Value": 90.0, "Nominal": 1}}},
        "rates_payload": {"Valute": {"USD": {"Value": 90.0, "Nominal": 1}}},
        "empty_symbol_payload": {},
        "direct_symbol": "USDRUB",
        "reverse_symbol": "RUBUSD",
        "direct_course": 90.0,
    },
    {
        "id": "garantex",
        "module": garantex,
        "settings_attr": "garantex",
        "fetch_symbols": garantex.fetch_garantex_symbols,
        "fetch_rates": garantex.fetch_garantex_rates,
        "symbol_payload": [{"ask_unit": "usdt", "bid_unit": "rub"}],
        "rates_payload": [{"price": "100.0"}],
        "empty_symbol_payload": [],
        "direct_symbol": "USDTRUB",
        "reverse_symbol": "RUBUSDT",
        "direct_course": 100.0,
    },
]


@pytest.mark.parametrize("case", SPOT_CASES, ids=[case["id"] for case in SPOT_CASES])
def test_spot_integrations_return_direct_and_reverse_rates(
    monkeypatch,
    run_async,
    market_factory,
    rates_by_symbol,
    case,
):
    calls = []

    async def fake_fetch_data(url, *args, **kwargs):
        calls.append(url)
        if len(calls) == 1:
            return case["symbol_payload"]
        if case["id"] == "garantex" and f"market={case['direct_symbol'].lower()}" not in url:
            return []
        return case["rates_payload"]

    monkeypatch.setattr(case["module"], "fetch_data", fake_fetch_data)
    market = market_factory(case["settings_attr"])

    symbols = run_async(case["fetch_symbols"](market))
    rates = run_async(case["fetch_rates"](market))

    assert [symbol.symbol for symbol in symbols] == [case["direct_symbol"]]
    assert {symbol.symbol for symbol in market.symbols} == {
        case["direct_symbol"],
        case["reverse_symbol"],
    }

    by_symbol = rates_by_symbol(rates)
    assert set(by_symbol) == {case["direct_symbol"], case["reverse_symbol"]}
    assert by_symbol[case["direct_symbol"]].stock_market == market.name
    assert by_symbol[case["direct_symbol"]].course == pytest.approx(case["direct_course"])
    assert by_symbol[case["reverse_symbol"]].course == pytest.approx(1 / case["direct_course"])


@pytest.mark.parametrize("case", SPOT_CASES, ids=[case["id"] for case in SPOT_CASES])
def test_spot_symbol_fetch_returns_empty_list_for_empty_payload(
    monkeypatch,
    run_async,
    market_factory,
    case,
):
    async def fake_fetch_data(url, *args, **kwargs):
        return case["empty_symbol_payload"]

    monkeypatch.setattr(case["module"], "fetch_data", fake_fetch_data)
    market = market_factory(case["settings_attr"])

    symbols = run_async(case["fetch_symbols"](market))

    assert symbols == []
    assert market.symbols == []
