# app/forex_scraper_service.py

import time
from datetime import datetime

import json
# from sqlalchemy.orm import Session
# from sqlalchemy import text

from utility.common_utility import (
    setup_logger, settings, PAIR_CONFIG,
    # ForexHistoricalData, CurrencyPair,
    # upsert_forex_data
)
from utility.currency_scrape import scrape_pair
from app.currency_schema import (
    ScrapeRequest, ScrapeResponse, ScrapeResult,
    DataResponse, ForexRecord, PairsListResponse
)

logger = setup_logger("currency_scrape.service")


# ============================================================
# SCRAPE SERVICE
# ============================================================

def run_scrape(request: ScrapeRequest) -> ScrapeResponse:
    """
    Orchestrates the full scrape for the requested pairs.
    Saves results to DB. Returns a detailed summary response.
    """
    start_time = time.time()

    start_date = request.start_date or settings.START_DATE
    end_date   = request.end_date   or datetime.now().strftime('%Y-%m-%d')

    logger.info(f"Scrape started | Pairs: {request.pairs} | {start_date} -> {end_date}")

    results = []
    total_records = 0
    all_data = {}

    for pair_key in request.pairs:
        # Validate the pair exists in our config
        if pair_key not in PAIR_CONFIG:
            logger.error(f"Unknown pair key: {pair_key}")
            results.append(ScrapeResult(
                pair_key=pair_key, status='failed',
                records_saved=0, date_from=None, date_to=None,
                error=f"Unknown pair '{pair_key}'"
            ))
            continue

        cfg = PAIR_CONFIG[pair_key]

        try:
            record = None
            for attempt in range(3):
                try:
                # Scrape the pair
                    records = scrape_pair(
                        pair_key    = pair_key,
                        investing_id= cfg['id'],
                        slug        = cfg['slug'],
                        start_date  = start_date,
                        end_date    = end_date
                    )
                    break
                except Exception as e:
                    if "HTTP 429" in str(e):
                        wait = 60 * (attempt + 1)  # 60s → 120s → 180s
                        logger.warning(f"[{pair_key}] 429 received, waiting {wait}s (attempt {attempt + 1}/3)...")
                        time.sleep(wait)
                        if attempt == 2:
                            raise  # re-raise after final attempt
                    else:
                        raise  # non-429 error, fail immediately

            if not records:
                raise Exception("Scraper returned 0 records")

            all_data[pair_key] = records
            total_records += len(records)

            # Save to DB
            # saved_count = upsert_forex_data(db, records)
            # total_records += saved_count

            results.append(ScrapeResult(
                pair_key      = pair_key,
                status        = 'success',
                records_saved = len(records),
                date_from     = records[0]['date'],
                date_to       = records[-1]['date']
            ))
            logger.info(f"[{pair_key}] OK {len(records)} records scraped")

        except Exception as e:
            logger.error(f"[{pair_key}] Failed: {e}")
            results.append(ScrapeResult(
                pair_key=pair_key, status='failed',
                records_saved=0, date_from=None, date_to=None,
                error=str(e)
            ))

        # Delay between pairs
        if pair_key != request.pairs[-1]:
            import random
            delay = random.uniform(settings.SCRAPE_DELAY_MIN, settings.SCRAPE_DELAY_MAX)
            logger.info(f"Waiting {delay:.1f}s before next pair...")
            time.sleep(delay)

    if all_data:
        filename = f"forex_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data saved to {filename}")

    duration = round(time.time() - start_time, 2)
    successful = sum(1 for r in results if r.status == 'success')
    failed     = sum(1 for r in results if r.status == 'failed')

    duration = round(time.time() - start_time, 2)
    successful = sum(1 for r in results if r.status == 'success')
    failed     = sum(1 for r in results if r.status == 'failed')

    logger.info(f"Scrape complete | {successful}/{len(request.pairs)} pairs | {total_records} records | {duration}s")

    return ScrapeResponse(
        total_pairs   = len(request.pairs),
        successful    = successful,
        failed        = failed,
        total_records = total_records,
        results       = results,
        duration_secs = duration
    )


# ============================================================
# DATA QUERY SERVICE
# ============================================================

# def get_forex_data(pair_key: str, start_date: str = None,
#                    end_date: str = None, limit: int = None,
#                     ) -> DataResponse:
#     """
#     Fetches historical data from DB for a given pair.
#     Supports date range filtering and row limit.
#     """
#     # query = db.query(ForexHistoricalData).filter(
#     #     ForexHistoricalData.pair_key == pair_key.upper()
#     # )
#
#     if start_date:
#         query = query.filter(ForexHistoricalData.date >= start_date)
#     if end_date:
#         query = query.filter(ForexHistoricalData.date <= end_date)
#
#     query = query.order_by(ForexHistoricalData.date.asc())
#
#     if limit:
#         query = query.limit(limit)
#
#     rows = query.all()
#
#     if not rows:
#         return DataResponse(
#             pair_key=pair_key, total_records=0,
#             date_from=None, date_to=None, data=[]
#         )
#
#     records = [ForexRecord.model_validate(row) for row in rows]
#
#     return DataResponse(
#         pair_key      = pair_key,
#         total_records = len(records),
#         date_from     = str(records[0].date),
#         date_to       = str(records[-1].date),
#         data          = records
#     )


# ============================================================
# PAIRS LIST SERVICE
# ============================================================

def get_all_pairs() -> PairsListResponse:
    """Returns all active currency pairs from the master table."""
    # pairs = db.query(CurrencyPair).filter_by(is_active=True).all()
    return PairsListResponse(
        total = len(PAIR_CONFIG),
        pairs = [
            {
                'pair_key':    k,
                'display_name': v['name'],
                'base_currency': v['base'],
                'quote_currency': v['quote'],
                'investing_id': v['id']
            }
            for k, v in PAIR_CONFIG.items()
        ]
    )


# ============================================================
# HEALTH CHECK SERVICE
# ============================================================

def check_health() -> dict:
    """Pings the database to verify connectivity."""
    # try:
    #     db.execute(text("SELECT 1"))
    #     db_status = "connected"
    # except Exception as e:
    #     db_status = f"error: {e}"

    return {
        "status":   "ok",
        "database": "not connected (disabled)",
        # "database": db_status,
        "message":  "Forex Scraper Microservice is running"
    }