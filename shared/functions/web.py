import logging

from ddgs import DDGS

logger = logging.getLogger(__name__)


def search(query: str) -> str:
    """Performs a web search and returns the top results."""
    logger.info("Searching the web for: %s", query)
    try:
        results = DDGS().text(query, max_results=10)
        if not results:
            return "No results found."
        return "\n\n".join(f"{r['title']}\n{r['href']}\n{r['body']}" for r in results)
    except Exception as e:
        return f"Search failed: {e}"
