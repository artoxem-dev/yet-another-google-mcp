import re
from typing import Any, Dict, Optional

EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


def validate_email(email: str) -> bool:
    """Validate email format."""
    return re.match(EMAIL_REGEX, email) is not None


def require_auth(arguments: Dict[str, Any], auth_token: Optional[str]) -> None:
    """Require MCP_AUTH_TOKEN to be set for all tool calls."""
    if not auth_token:
        raise ValueError(
            "MCP_AUTH_TOKEN is not set. Set environment variable MCP_AUTH_TOKEN "
            "to enable MCP access."
        )
