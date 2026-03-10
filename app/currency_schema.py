# app/forex_scraper_schema.py

from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


# ============================================================
# REQUEST SCHEMAS — What the API accepts as input
# ============================================================

class ScrapeRequest(BaseModel):
    """Body for POST /scrape"""
    pairs: list[str] = Field(
        default=['USDINR', 'EURINR', 'GBPINR', 'USDJPY', 'EURUSD', 'GBPUSD', 'JPYINR'],
        description="List of pair keys to scrape. Defaults to all 7 pairs."
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Override start date YYYY-MM-DD. Defaults to .env START_DATE."
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Override end date YYYY-MM-DD. Defaults to today."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "pairs": ["USDINR", "EURUSD"],
                "start_date": "2023-01-01",
                "end_date": "2024-12-31"
            }
        }


class DataQueryRequest(BaseModel):
    """Query params for GET /data"""
    pair_key:   str
    start_date: Optional[str] = None
    end_date:   Optional[str] = None
    limit:      Optional[int] = Field(default=None, ge=1, le=5000)


# ============================================================
# RESPONSE SCHEMAS — What the API returns as output
# ============================================================

class ForexRecord(BaseModel):
    """One row of OHLC data"""
    pair_key:    str
    date:        date
    open_price:  float
    high_price:  float
    low_price:   float
    close_price: float
    change_pct:  Optional[float]

    class Config:
        from_attributes = True   # Allows creating from SQLAlchemy ORM objects


class ScrapeResult(BaseModel):
    """Result for one pair after scraping"""
    pair_key:       str
    status:         str           # 'success' | 'failed'
    records_saved:  int
    date_from:      Optional[str]
    date_to:        Optional[str]
    error:          Optional[str] = None


class ScrapeResponse(BaseModel):
    """Full response for POST /scrape"""
    total_pairs:    int
    successful:     int
    failed:         int
    total_records:  int
    results:        list[ScrapeResult]
    duration_secs:  float


class DataResponse(BaseModel):
    """Response for GET /data/{pair_key}"""
    pair_key:      str
    total_records: int
    date_from:     Optional[str]
    date_to:       Optional[str]
    data:          list[ForexRecord]


class PairsListResponse(BaseModel):
    """Response for GET /pairs"""
    total: int
    pairs: list[dict]


class HealthResponse(BaseModel):
    """Response for GET /health"""
    status:   str
    database: str
    message:  str