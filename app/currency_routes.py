# app/forex_scraper_route.py

from fastapi import APIRouter, Depends, Query, HTTPException
# from sqlalchemy.orm import Session
from typing import Optional

# from utility.common_utility import get_db
from app.currency_schema import (
    ScrapeRequest, ScrapeResponse,
    DataResponse, PairsListResponse, HealthResponse
)
from app.currency_service import (
    run_scrape,
    get_all_pairs, check_health
)

router = APIRouter(prefix="/forex", tags=["Forex Scraper"])


# ============================================================
# HEALTH CHECK
# GET /forex/health
# ============================================================

@router.get("/health", response_model=HealthResponse)
def health_check():
    """Check if the service and database are running."""
    result = check_health()
    return result


# ============================================================
# GET ALL PAIRS
# GET /forex/pairs
# ============================================================

@router.get("/pairs", response_model=PairsListResponse)
def list_pairs():
    """Returns all active currency pairs in the system."""
    return get_all_pairs()


# ============================================================
# TRIGGER SCRAPE
# POST /forex/scrape
# ============================================================

@router.post("/scrape", response_model=ScrapeResponse)
def trigger_scrape(
    request: ScrapeRequest,
):
    """
    Triggers a scrape from Investing.com for the specified pairs.
    Saves results to the database.
    Returns a detailed summary of what was scraped.
    """
    return run_scrape(request)


# ============================================================
# GET HISTORICAL DATA
# GET /forex/data/{pair_key}
# ============================================================

# @router.get("/data/{pair_key}", response_model=DataResponse)
# def get_data(
#     pair_key:   str,
#     start_date: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
#     end_date:   Optional[str] = Query(default=None, description="YYYY-MM-DD"),
#     limit:      Optional[int] = Query(default=None, ge=1, le=5000),
#     db: Session = Depends(get_db)
# ):
#     """
#     Returns historical OHLC data for a specific currency pair.
#     Optionally filter by date range or limit number of rows.
#     """
#     pair_key = pair_key.upper()
#     return get_forex_data(pair_key, start_date, end_date, limit, db)
#
#
# # ============================================================
# # GET LATEST PRICE
# # GET /forex/data/{pair_key}/latest
# # ============================================================
#
# @router.get("/data/{pair_key}/latest")
# def get_latest(
#     pair_key: str,
#     db: Session = Depends(get_db)
# ):
#     """Returns the single most recent record for a pair."""
#     result = get_forex_data(
#         pair_key   = pair_key,
#         start_date = None,
#         end_date   = None,
#         limit      = 1,
#         db         = db
#     )
#     if not result.data:
#         raise HTTPException(status_code=404, detail=f"No data found for {pair_key}")
#
#     # Return just the last record (query is ASC, so reverse)
#     from utility.common_utility import ForexHistoricalData
#     row = db.query(ForexHistoricalData)\
#             .filter_by(pair_key=pair_key.upper())\
#             .order_by(ForexHistoricalData.date.desc())\
#             .first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail=f"No data found for {pair_key}")
#
#     return {
#         "pair_key":    row.pair_key,
#         "date":        str(row.date),
#         "open_price":  float(row.open_price),
#         "high_price":  float(row.high_price),
#         "low_price":   float(row.low_price),
#         "close_price": float(row.close_price),
#         "change_pct":  float(row.change_pct) if row.change_pct else None
#     }