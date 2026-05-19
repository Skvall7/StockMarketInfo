import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config.app import log_execution_time
from config.config import settings, all_rates
from smi.integration.binance import fetch_binance_symbols, fetch_binance_rates
from smi.integration.binance_p2p import fetch_binance_p2p_symbols, fetch_binance_p2p_rates
from smi.integration.bybit import fetch_bybit_symbols, fetch_bybit_rates
from smi.integration.bybit_p2p import fetch_bybit_p2p_rates, fetch_bybit_p2p_symbols
from smi.integration.cbr import fetch_cbr_symbols, fetch_cbr_rates
from smi.integration.garantex import fetch_garantex_symbols, fetch_garantex_rates
from smi.integration.goatx import fetch_goatx_symbols, fetch_goatx_rates
from smi.integration.htx import fetch_htx_symbols, fetch_htx_rates
from smi.integration.payeer import fetch_payeer_symbols, fetch_payeer_rates
from smi.integration.rapira import fetch_rapira_symbols, fetch_rapira_rates
from smi.integration.wmg import fetch_wmg_symbols, fetch_wmg_rates
from smi.routes import include_routes
from smi.schemas import Symbol

logger = logging.getLogger(settings.title)


@log_execution_time
async def collect_rates(fetch_function, stock_market):
    rates = await fetch_function(stock_market)
    for rate in rates:
        all_rates[(rate.stock_market, rate.symbol)] = rate

async def update_course(stock_market, fetch_course_func):
    """Обновляет курсы бирж с заданным интервалом."""
    while True:
        try:
            await collect_rates(fetch_course_func, stock_market)
        except Exception as e:
            logger.warning(f"Failed to update {stock_market.name}: {e}")
        await asyncio.sleep(stock_market.requests_sleep)

async def update_info():
    """Обновляет символы биржи с заданным интервалом."""
    while True:
        await fetch_all_symbols()
        await asyncio.sleep(600)

async def fetch_all_symbols() -> list[Symbol]:
    fetch_tasks = [
        # fetch_binance_symbols(settings.binance),
        # fetch_garantex_symbols(settings.garantex),
        fetch_payeer_symbols(settings.payeer),
        # fetch_htx_symbols(settings.htx),
        # fetch_cbr_symbols(settings.cbr),
        # fetch_wmg_symbols(settings.wmg),
        fetch_goatx_symbols(settings.goatx),
        # fetch_bybit_symbols(settings.bybit),
        fetch_bybit_p2p_symbols(settings.bybit_p2p),
        fetch_rapira_symbols(settings.rapira),
        fetch_binance_p2p_symbols(settings.binance_p2p),
    ]
    results = await asyncio.gather(*fetch_tasks)
    symbol_set = {symbol.symbol: symbol for symbol_list in results for symbol in symbol_list}
    return list(symbol_set.values())

@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = [
        asyncio.create_task(update_info()),
        # asyncio.create_task(update_course(settings.binance, fetch_binance_rates)),
        # asyncio.create_task(update_course(settings.garantex, fetch_garantex_rates)),
        asyncio.create_task(update_course(settings.payeer, fetch_payeer_rates)),
        # asyncio.create_task(update_course(settings.htx, fetch_htx_rates)),
        # asyncio.create_task(update_course(settings.cbr, fetch_cbr_rates)),
        # asyncio.create_task(update_course(settings.wmg, fetch_wmg_rates)),
        asyncio.create_task(update_course(settings.goatx, fetch_goatx_rates)),
        # asyncio.create_task(update_course(settings.bybit, fetch_bybit_rates)),
        asyncio.create_task(update_course(settings.bybit_p2p, fetch_bybit_p2p_rates)),
        asyncio.create_task(update_course(settings.rapira, fetch_rapira_rates)),
        asyncio.create_task(update_course(settings.binance_p2p, fetch_binance_p2p_rates)),
    ]
    yield  # Запуск приложения

app = FastAPI(
    title=settings.title,
    description=settings.description,
    version=settings.version,
    lifespan=lifespan
)

include_routes(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001)
