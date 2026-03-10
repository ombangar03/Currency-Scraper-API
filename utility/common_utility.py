# utility/common_utility.py

import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
# from sqlalchemy import create_engine, Column, String, Date, Numeric, BigInteger, Boolean, TIMESTAMP, text
# from sqlalchemy.orm import sessionmaker, DeclarativeBase
# from sqlalchemy.dialects.postgresql import insert as pg_insert

load_dotenv()

# ============================================================
# CONFIGURATION — Reads from .env file
# ============================================================

class Settings(BaseSettings):
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "forex_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""

    # Scraper
    START_DATE: str = "2020-01-01"
    SCRAPE_DELAY_MIN: float = 4.0
    SCRAPE_DELAY_MAX: float = 8.0
    COOKIE_DELAY_MIN: float = 2.0
    COOKIE_DELAY_MAX: float = 4.0
    REQUEST_TIMEOUT_PAGE: int = 15
    REQUEST_TIMEOUT_API: int = 30
    BROWSER_IMPERSONATE: str = "chrome110"

    # App
    APP_HOST: str = "localhost"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


# Single instance used across the entire app
settings = Settings()


# ============================================================
# LOGGING — Writes to both console and app.log
# ============================================================

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler — prints to terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # File handler — writes to app.log
    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger






# ============================================================
# DATABASE — SQLAlchemy setup
# ============================================================

# DATABASE_URL = (
#     f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
#     f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
# )
#
# engine = create_engine(
#     DATABASE_URL,
#     pool_size=5,          # Max 5 persistent connections in the pool
#     max_overflow=10,      # Up to 10 extra connections allowed temporarily
#     pool_pre_ping=True,   # Test connection before using it (handles dropped connections)
#     echo=False            # Set True to print all SQL queries (useful for debugging)
# )
#
# SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
#
#
# # ============================================================
# # ORM MODELS — Python classes that map to DB tables
# # ============================================================
#
# class Base(DeclarativeBase):
#     pass
#
#
# class CurrencyPair(Base):
#     __tablename__ = "currency_pairs"
#
#     id             = Column(BigInteger, primary_key=True, autoincrement=True)
#     pair_key       = Column(String(10),  nullable=False, unique=True)
#     base_currency  = Column(String(5),   nullable=False)
#     quote_currency = Column(String(5),   nullable=False)
#     display_name   = Column(String(20),  nullable=False)
#     investing_id   = Column(String(10),  nullable=False)
#     slug           = Column(String(30),  nullable=False)
#     is_active      = Column(Boolean,     default=True)
#     created_at     = Column(TIMESTAMP,   default=datetime.now)
#
#
# class ForexHistoricalData(Base):
#     __tablename__ = "forex_historical_data"
#
#     id          = Column(BigInteger, primary_key=True, autoincrement=True)
#     pair_key    = Column(String(10),     nullable=False)
#     date        = Column(Date,           nullable=False)
#     open_price  = Column(Numeric(20, 6), nullable=False)
#     high_price  = Column(Numeric(20, 6), nullable=False)
#     low_price   = Column(Numeric(20, 6), nullable=False)
#     close_price = Column(Numeric(20, 6), nullable=False)
#     change_pct  = Column(Numeric(10, 4))
#     scraped_at  = Column(TIMESTAMP, default=datetime.now)
#
#
# # ============================================================
# # DATABASE UTILITIES
# # ============================================================
#
# def get_db():
#     """
#     Dependency function for FastAPI routes.
#     Yields a DB session and guarantees it's closed after use.
#     Used with FastAPI's Depends() system.
#     """
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
#
#
# def create_tables():
#     """Creates all tables if they don't already exist."""
#     Base.metadata.create_all(bind=engine)
#
#
# def upsert_forex_data(db, records: list[dict]):
#     """
#     Inserts rows. If (pair_key, date) already exists, updates it.
#     This is PostgreSQL's ON CONFLICT DO UPDATE — called an upsert.
#     Prevents duplicate rows when re-running the scraper.
#     """
#     if not records:
#         return 0
#
#     stmt = pg_insert(ForexHistoricalData).values(records)
#     stmt = stmt.on_conflict_do_update(
#         index_elements=['pair_key', 'date'],
#         set_={
#             'open_price':  stmt.excluded.open_price,
#             'high_price':  stmt.excluded.high_price,
#             'low_price':   stmt.excluded.low_price,
#             'close_price': stmt.excluded.close_price,
#             'change_pct':  stmt.excluded.change_pct,
#             'scraped_at':  datetime.now()
#         }
#     )
#     db.execute(stmt)
#     db.commit()
#     return len(records)
#
#
# # Seed data — the 7 pairs we want

#
#
# def seed_currency_pairs(db):
#     """Inserts the 7 currency pairs into the master table if they don't exist."""
#     for pair_key, cfg in PAIR_CONFIG.items():
#         exists = db.query(CurrencyPair).filter_by(pair_key=pair_key).first()
#         if not exists:
#             db.add(CurrencyPair(
#                 pair_key       = pair_key,
#                 base_currency  = cfg['base'],
#                 quote_currency = cfg['quote'],
#                 display_name   = cfg['name'],
#                 investing_id   = cfg['id'],
#                 slug           = cfg['slug']
#             ))
#     db.commit()

PAIR_CONFIG = {
    'USDINR': {'id': '160',  'base': 'USD', 'quote': 'INR', 'name': 'USD/INR', 'slug': 'usd-inr'},
    'EURINR': {'id': '1619', 'base': 'EUR', 'quote': 'INR', 'name': 'EUR/INR', 'slug': 'eur-inr'},
    'GBPINR': {'id': '1621', 'base': 'GBP', 'quote': 'INR', 'name': 'GBP/INR', 'slug': 'gbp-inr'},
    'USDJPY': {'id': '3',    'base': 'USD', 'quote': 'JPY', 'name': 'USD/JPY', 'slug': 'usd-jpy'},
    'EURUSD': {'id': '1',    'base': 'EUR', 'quote': 'USD', 'name': 'EUR/USD', 'slug': 'eur-usd'},
    'GBPUSD': {'id': '2',    'base': 'GBP', 'quote': 'USD', 'name': 'GBP/USD', 'slug': 'gbp-usd'},
    'JPYINR': {'id': '1624', 'base': 'JPY', 'quote': 'INR', 'name': 'JPY/INR', 'slug': 'jpy-inr'},
}