import logging
import os

logger = logging.getLogger(__name__)


def setup_logging(level=logging.WARNING):
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(fmt)

    file_handler = logging.FileHandler("langgraph-example.log")
    file_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(console)
    root.addHandler(file_handler)


def setup_tracing():
    if os.environ.get("LANGCHAIN_API_KEY"):
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault("LANGCHAIN_PROJECT", "langgraph-example")
        logger.info(
            "LangSmith tracing enabled (project: %s)", os.environ["LANGCHAIN_PROJECT"]
        )
    else:
        logger.info("LangSmith tracing disabled (set LANGCHAIN_API_KEY to enable)")
