"""
Scrapers package for JAV movie sites.

Provides scrapers for:
- JavBus: Using scrapling library
- JavDB: Using curl_cffi with API support
"""

from .javbus_scraper import JavBusScraper
from .javdb_scraper import JavDBApiScraper

__all__ = ["JavBusScraper", "JavDBApiScraper"]
