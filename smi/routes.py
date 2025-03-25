from fastapi import APIRouter, FastAPI

from config.config import settings, all_rates
from smi.schemas import StockMarket, SMCourse

def include_routes(app: FastAPI) -> None:
    app.include_router(info_router, prefix="/sm-info", tags=["Info"])
    app.include_router(rates_router, prefix="/sm-rates", tags=["Rates"])

info_router = APIRouter()

@info_router.get("", response_model=list[StockMarket])
def get_markets():
    return [
        settings.binance,
        settings.garantex,
        settings.payeer,
        settings.htx,
        settings.cbr,
        settings.wmg
    ]


rates_router = APIRouter()

@rates_router.get("", response_model=list[SMCourse])
async def get_rates(sm: str = None, symbol: str = None):
    filtered_rates = [rate for key, rate in all_rates.items()]
    if sm:
        filtered_rates = [rate for rate in filtered_rates if rate.stock_market.lower() == sm.lower()]
    if symbol:
        filtered_rates = [rate for rate in filtered_rates if rate.symbol.lower() == symbol.lower()]
    return filtered_rates