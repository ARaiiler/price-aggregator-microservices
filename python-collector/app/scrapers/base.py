"""
Abstract base class for all product scrapers.

Every scraper must implement ``fetch`` so the collector service can
treat all sources uniformly without knowing their internal details.
"""
import abc
import logging
from typing import List

from app.models.product import SourceResult

logger = logging.getLogger(__name__)


class BaseScraper(abc.ABC):
    """
    Abstract scraper interface.

    Attributes
    ----------
    source_name : str
        Human-readable name used in logs and response payloads.
    base_url : str
        Root URL of the data source (used for constructing product URLs).
    """

    source_name: str = "UnnamedSource"
    base_url: str = ""

    @abc.abstractmethod
    async def fetch(self, product_name: str) -> List[SourceResult]:
        """
        Fetch product listings for *product_name* from this source.

        Parameters
        ----------
        product_name:
            The search query as entered by the end user.

        Returns
        -------
        List[SourceResult]
            Zero or more raw (un-normalised) results.  An empty list is a
            valid response when the source returns no matching products.

        Raises
        ------
        Exception
            Implementations should let network / parsing exceptions
            propagate so the collector service can handle them centrally.
        """

    async def safe_fetch(self, product_name: str) -> List[SourceResult]:
        """
        Wrapper around ``fetch`` that catches all exceptions and returns an
        empty list on failure.

        This ensures a single failing source never prevents other sources
        from contributing to the final response.
        """
        try:
            return await self.fetch(product_name)
        except Exception as exc:
            logger.warning(
                "Scraper %s failed for query '%s': %s",
                self.source_name,
                product_name,
                exc,
            )
            return []
