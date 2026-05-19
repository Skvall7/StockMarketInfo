import pytest

from smi.integration import goatx, wmg


STATIC_CASES = [
    (
        "wmg",
        wmg.fetch_wmg_symbols,
        wmg.fetch_wmg_rates,
        "USDTUSD",
        "USDUSDT",
        1.0,
    ),
    (
        "goatx",
        goatx.fetch_goatx_symbols,
        goatx.fetch_goatx_rates,
        "USDTAZN",
        "AZNUSDT",
        1.75,
    ),
]


@pytest.mark.parametrize(
    "settings_attr, fetch_symbols, fetch_rates, direct_symbol, reverse_symbol, direct_course",
    STATIC_CASES,
    ids=[case[0] for case in STATIC_CASES],
)
def test_static_integrations_return_direct_and_reverse_rates(
    run_async,
    market_factory,
    rates_by_symbol,
    settings_attr,
    fetch_symbols,
    fetch_rates,
    direct_symbol,
    reverse_symbol,
    direct_course,
):
    market = market_factory(settings_attr)

    symbols = run_async(fetch_symbols(market))
    rates = run_async(fetch_rates(market))

    assert [symbol.symbol for symbol in symbols] == [direct_symbol]
    assert {symbol.symbol for symbol in market.symbols} == {direct_symbol, reverse_symbol}

    by_symbol = rates_by_symbol(rates)
    assert set(by_symbol) == {direct_symbol, reverse_symbol}
    assert by_symbol[direct_symbol].stock_market == market.name
    assert by_symbol[direct_symbol].course == pytest.approx(direct_course)
    assert by_symbol[direct_symbol].calculated is False
    assert by_symbol[reverse_symbol].course == pytest.approx(1 / direct_course)
    assert by_symbol[reverse_symbol].calculated is True
