"""
Scrapers package.

Each scraper module implements ``BaseScraper`` and is responsible for
fetching price data from exactly one source.

New sources are added by:
1. Creating a new module in this package that subclasses ``BaseScraper``.
2. Registering the class in ``collector_service.py``.
"""
from .base import BaseScraper
from .source_a import FnacScraper
from .source_b import JumiaScraper

__all__ = ["BaseScraper", "FnacScraper", "JumiaScraper"]
