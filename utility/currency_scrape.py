# utility/forex_scraper_scrape.py

import time
import random
from datetime import datetime
from curl_cffi import requests as cf_requests
from utility.common_utility import setup_logger, settings

logger = setup_logger("forex_scraper.scrape")


# ============================================================
# DATE PARSER
# ============================================================

def parse_date(raw_date: str) -> str:
    """
    Converts any date format Investing.com returns → 'YYYY-MM-DD'
    Investing.com commonly returns: 'Apr 03, 2020'
    """
    raw_date = str(raw_date).strip()

    formats_to_try = [
        '%b %d, %Y',   # Apr 03, 2020
        '%Y-%m-%d',    # 2020-04-03
        '%m/%d/%Y',    # 04/03/2020
        '%d/%m/%Y',    # 03/04/2020
        '%B %d, %Y',   # April 03, 2020
    ]

    for fmt in formats_to_try:
        try:
            return datetime.strptime(raw_date, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue

    logger.warning(f"Could not parse date '{raw_date}' — returning raw")
    return raw_date


# ============================================================
# HEADERS BUILDER
# ============================================================

# REPLACE the entire get_headers function with this:

BROWSER_PROFILES = [
    {
        'impersonate': 'chrome110',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    },
    {
        'impersonate': 'chrome107',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    },
    {
        'impersonate': 'chrome104',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
    },
    {
        'impersonate': 'safari15_5',
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15'
    },
]

def get_headers(slug: str, user_agent: str) -> dict:
    return {
        'User-Agent':       user_agent,
        'Accept':           'application/json, text/plain, */*',
        'Accept-Language':  'en-US,en;q=0.9',
        'Accept-Encoding':  'gzip, deflate, br',
        'Referer':          f'https://www.investing.com/currencies/{slug}',
        'Origin':           'https://www.investing.com',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection':       'keep-alive',
        'domain-id':        'www',
        'Sec-Fetch-Dest':   'empty',
        'Sec-Fetch-Mode':   'cors',
        'Sec-Fetch-Site':   'same-origin',
        'DNT':              '1',
    }


# ============================================================
# FETCH ONE PAIR
# ============================================================

def fetch_pair_raw(pair_key: str, investing_id: str, slug: str,
                   start_date: str, end_date: str) -> dict:

    api_url = (
        f"https://api.investing.com/api/financialdata/historical/{investing_id}"
        f"?start-date={start_date}"
        f"&end-date={end_date}"
        f"&time-frame=Daily"
        f"&add-missing-rows=false"
    )

    for attempt in range(3):
        # Pick a random browser profile on every attempt
        profile = random.choice(BROWSER_PROFILES)
        impersonate = profile['impersonate']
        user_agent  = profile['user_agent']

        # Fresh session every attempt
        session = cf_requests.Session()

        # Step 1: Cookie priming
        logger.info(f"[{pair_key}] Attempt {attempt+1}/3 | Priming cookies ({impersonate})...")
        try:
            session.get(
                f"https://www.investing.com/currencies/{slug}",
                headers={
                    'User-Agent':     user_agent,
                    'Accept':         'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language':'en-US,en;q=0.9',
                },
                impersonate=impersonate,
                timeout=settings.REQUEST_TIMEOUT_PAGE
            )
            delay = random.uniform(settings.COOKIE_DELAY_MIN, settings.COOKIE_DELAY_MAX)
            logger.info(f"[{pair_key}] Cookies primed. Waiting {delay:.1f}s...")
            time.sleep(delay)

        except Exception as e:
            logger.warning(f"[{pair_key}] Cookie priming warning: {e}")

        # Step 2: API call
        logger.info(f"[{pair_key}] Calling historical API...")
        response = session.get(
            api_url,
            headers=get_headers(slug, user_agent),
            impersonate=impersonate,
            timeout=settings.REQUEST_TIMEOUT_API
        )

        logger.info(f"[{pair_key}] Status: {response.status_code}")

        if response.status_code == 200:
            return response.json()

        elif response.status_code == 429:
            wait = 60 * (attempt + 1)  # 60s, 120s, 180s
            logger.warning(f"[{pair_key}] 429 received. Waiting {wait}s before retry...")
            time.sleep(wait)
            continue  # retry with fresh session + different profile

        elif response.status_code == 403:
            raise Exception(f"[{pair_key}] 403 Forbidden — Cloudflare hard block")

        elif response.status_code == 401:
            raise Exception(f"[{pair_key}] 401 Unauthorized — Login required")

        else:
            raise Exception(f"[{pair_key}] HTTP {response.status_code}: {response.text[:200]}")

    raise Exception(f"[{pair_key}] HTTP 429 — failed after 3 attempts with different profiles")

# ============================================================
# PARSE RESPONSE
# ============================================================

def parse_pair_response(raw_json: dict, pair_key: str, start_date: str) -> list[dict]:
    """
    Parses Investing.com API response into clean list of dicts
    ready for DB insertion.
    """
    if 'data' not in raw_json:
        raise Exception(f"[{pair_key}] No 'data' key. Got: {list(raw_json.keys())}")

    rows = raw_json['data']
    records = []

    for row in rows:
        try:
            raw_date = row.get('rowDate', row.get('date', ''))
            date_str = parse_date(raw_date)

            close = float(str(row.get('last_close', row.get('price', 0))).replace(',', ''))
            open_ = float(str(row.get('last_open',  row.get('open',  0))).replace(',', ''))
            high  = float(str(row.get('last_max',   row.get('high',  0))).replace(',', ''))
            low   = float(str(row.get('last_min',   row.get('low',   0))).replace(',', ''))

            change_pct = round((close - open_) / open_ * 100, 4) if open_ != 0 else 0.0

            records.append({
                'pair_key':    pair_key,
                'date':        date_str,        # Will be cast to DATE when inserted
                'open_price':  round(open_, 6),
                'high_price':  round(high,  6),
                'low_price':   round(low,   6),
                'close_price': round(close, 6),
                'change_pct':  change_pct
            })

        except Exception as e:
            logger.warning(f"[{pair_key}] Skipped malformed row: {row} | {e}")
            continue

    records.sort(key=lambda x: x['date'])
    records = [r for r in records if r['date'] >= start_date]

    return records


# ============================================================
# MAIN SCRAPE FUNCTION — Called by service.py
# ============================================================

def scrape_pair(pair_key: str, investing_id: str, slug: str,
                start_date: str, end_date: str) -> list[dict]:
    """
    Full scrape pipeline for one pair.
    Returns list of clean records ready for DB insertion.
    """
    raw_json = fetch_pair_raw(pair_key, investing_id, slug, start_date, end_date)
    records  = parse_pair_response(raw_json, pair_key, start_date)
    logger.info(f"[{pair_key}] Parsed {len(records)} records")
    return records