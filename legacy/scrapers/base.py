"""
Base scraper abstract class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class BaseScraper(ABC):
    """Abstract base class for scrapers."""

    def __init__(self, domains: List[str], min_delay: float = 3.0, max_delay: float = 6.0):
        self.domains = domains
        self.current_domain_index = 0
        self.min_delay = min_delay
        self.max_delay = max_delay

    def get_current_domain(self) -> str:
        """Get the current domain."""
        return self.domains[self.current_domain_index] if self.domains else ""

    def rotate_domain(self) -> str:
        """Rotate to the next domain and return it."""
        if self.domains:
            self.current_domain_index = (self.current_domain_index + 1) % len(self.domains)
        return self.get_current_domain()

    def reset_domain(self) -> str:
        """Reset to the first domain."""
        self.current_domain_index = 0
        return self.get_current_domain()

    @abstractmethod
    def search_movie(self, code: str) -> Optional[Dict[str, Any]]:
        """Search for a movie by code."""
        pass

    @abstractmethod
    def get_actor_page(self, actor_id: str, page: int = 1) -> Dict[str, Any]:
        """Get actor's movie page."""
        pass

    @abstractmethod
    def close(self):
        """Close the scraper session."""
        pass
