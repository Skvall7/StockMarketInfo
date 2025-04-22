import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config.app import log_execution_time
from config.config import settings, all_rates
from smi.parser import fetch_all_symbols, fetch_binance_rates, fetch_garantex_rates, fetch_payeer_rates, \
    fetch_htx_rates, fetch_cbr_rates, fetch_wmg_rates, fetch_bybit_rates, fetch_rapira_rates
from smi.routes import include_routes


@log_execution_time
async def collect_rates(fetch_function, stock_market):
    rates = await fetch_function(stock_market)
    for rate in rates:
        all_rates[(rate.stock_market, rate.symbol)] = rate

async def update_course(stock_market, fetch_course_func):
    """Обновляет курсы бирж с заданным интервалом."""
    while True:
        await collect_rates(fetch_course_func, stock_market)
        # print(f'Updated {stock_market.name} rates.')
        await asyncio.sleep(stock_market.requests_sleep)

async def update_info():
    """Обновляет символы биржи с заданным интервалом."""
    while True:
        await fetch_all_symbols()
        # print('Updated all symbols.')
        await asyncio.sleep(600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = [
        asyncio.create_task(update_info()),
        # asyncio.create_task(update_course(settings.binance, fetch_binance_rates)),
        # asyncio.create_task(update_course(settings.garantex, fetch_garantex_rates)),
        # asyncio.create_task(update_course(settings.payeer, fetch_payeer_rates)),
        # asyncio.create_task(update_course(settings.htx, fetch_htx_rates)),
        asyncio.create_task(update_course(settings.cbr, fetch_cbr_rates)),
        # asyncio.create_task(update_course(settings.wmg, fetch_wmg_rates)),
        asyncio.create_task(update_course(settings.bybit, fetch_bybit_rates)),
        asyncio.create_task(update_course(settings.rapira, fetch_rapira_rates)),
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
