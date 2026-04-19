import logging
import os

logger = logging.getLogger(__name__)


def setup_logging(level=logging.WARNING):
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(fmt)

    file_handler = logging.FileHandler("pydantic-ai-example.log")
    file_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(console)
    root.addHandler(file_handler)


def setup_tracing():
    """Sets up observability.

    PydanticAI integrates with Logfire for tracing. Set ``LOGFIRE_TOKEN`` to
    enable it.  LangSmith is no longer used.
    """
    if os.environ.get("LOGFIRE_TOKEN"):
        try:
            import logfire

            logfire.configure()
            logfire.instrument_pydantic_ai()
            logger.info("Logfire tracing enabled")
        except ImportError:
            logger.warning("LOGFIRE_TOKEN set but logfire package not installed")
    else:
        logger.info("Tracing disabled (set LOGFIRE_TOKEN to enable Logfire tracing)")
