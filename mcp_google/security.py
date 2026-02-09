import re
from typing import Optional

EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


def validate_email(email: str) -> bool:
    """Validate email format."""
    return re.match(EMAIL_REGEX, email) is not None


def require_token_configured(auth_token: Optional[str]) -> None:
    """Ensure MCP_AUTH_TOKEN is configured on the server side.

    This is a configuration check, not per-request client authentication.
    For STDIO-based MCP servers the transport is inherently local, so this
    guard simply makes sure the operator has consciously set a token before
    the server becomes operational.
    """
    if not auth_token:
        raise ValueError(
            "MCP_AUTH_TOKEN is not set. Set environment variable MCP_AUTH_TOKEN "
            "to enable MCP access."
        )
