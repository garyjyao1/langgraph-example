def extract_text(content) -> str:
    """Normalizes LangChain message content to a plain string.

    Some providers (e.g. Anthropic) return content as a list of typed blocks
    like [{"type": "text", "text": "..."}] instead of a bare string.
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
