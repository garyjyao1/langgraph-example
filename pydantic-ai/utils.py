def extract_text(content) -> str:
    """Normalizes agent response content to a plain string.

    PydanticAI returns ``result.output`` as a plain ``str`` for text-only
    agents, so this helper is mainly used for streaming chunks which may
    arrive as ``str`` or as a list of typed blocks from some providers.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""
