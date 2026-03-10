# main.py

import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
# from sqlalchemy.orm import Session

# from utility.common_utility import (
#     setup_logger, settings,
#     create_tables, SessionLocal, seed_currency_pairs
# )
from app.currency_routes import router

from utility.common_utility import settings, setup_logger

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

logger = setup_logger("forex_scraper.main")


# ============================================================
# LIFESPAN — Runs on startup and shutdown
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    logger.info("=" * 50)
    logger.info("Forex Scraper Microservice starting...")

    # logger.info("Creating database tables...")
    # create_tables()
    #
    # logger.info("Seeding currency pairs master data...")
    # db: Session = SessionLocal()
    # try:
    #     seed_currency_pairs(db)
    # finally:
    #     db.close()

    logger.info("Startup complete. Server ready.")
    logger.info("=" * 50)

    yield  # App runs here

    # SHUTDOWN
    logger.info("Forex Scraper Microservice shutting down...")


# ============================================================
# APP INITIALIZATION
# ============================================================

app = FastAPI(
    title       = "Forex Scraper Microservice",
    description = "Scrapes historical forex data from Investing.com and stores it in PostgreSQL",
    version     = "1.0.0",
    lifespan    = lifespan
)

# Register all routes under /forex
app.include_router(router)


# Root redirect
@app.get("/")
def root():
    return {
        "service": "Forex Scraper Microservice",
        "version": "1.0.0",
        "docs":    "/docs",
        "health":  "/forex/health"
    }


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host    = settings.APP_HOST,
        port    = settings.APP_PORT,
        reload  = True,       # Auto-restart on code changes (dev mode)
        log_level = "info"
    )


## How Everything Connects — The Complete Flow

"""POST /forex/scrape
        ↓
forex_scraper_route.py  →  trigger_scrape(request, db)
        ↓
forex_scraper_service.py →  run_scrape(request, db)
        ↓ (for each pair)
forex_scraper_scrape.py  →  scrape_pair(pair_key, id, slug, dates)
        ↓
fetch_pair_raw()  →  curl_cffi hits Investing.com
        ↓
parse_pair_response()  →  cleans the data
        ↓ (back in service)
upsert_forex_data(db, records)  →  saves to PostgreSQL
        ↓
ScrapeResponse returned to client"""