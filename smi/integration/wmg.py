import logging

from config.app import log_execution_time
from config.config import settings
from smi.parser import process_market_data
from smi.schemas import StockMarket, SMCourse, Symbol

logger = logging.getLogger(settings.title)


@log_execution_time
async def fetch_wmg_symbols(stock_market: StockMarket) -> list[Symbol]:
    symbols = [Symbol(asset_left='USDT', asset_right='USD')]
    rev_symbols = [Symbol(asset_left=symbol.asset_right, asset_right=symbol.asset_left) for symbol in symbols]
    stock_market.symbols = []
    stock_market.symbols = symbols + rev_symbols
    return symbols

@log_execution_time
async def fetch_wmg_rates(stock_market: StockMarket) -> list[SMCourse]:
    return await process_market_data(
        stock_market,
        [{'symbol': 'USDTUSD', 'value': 1}],
        extract_symbol=lambda item: item['symbol'].upper(),
        extract_price=lambda item: float(item['value'])
    )
