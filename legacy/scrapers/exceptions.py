"""
Scraper exceptions.
"""


class ScrapingError(Exception):
    """Base exception for scraping errors."""
    pass


class RateLimitError(ScrapingError):
    """Raised when rate limited (429, 503, etc)."""
    pass


class DomainUnavailableError(ScrapingError):
    """Raised when all domains for a site are unavailable."""
    pass


class MovieNotFoundError(ScrapingError):
    """Raised when a movie is not found on the site."""
    pass
