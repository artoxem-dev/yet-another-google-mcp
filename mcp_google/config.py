import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/script.deployments",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
]


@dataclass(frozen=True)
class Config:
    client_secrets_file: str
    token_file: str
    backup_dir: str
    log_file: Optional[str]
    mcp_auth_token: Optional[str]
    scopes: List[str]


def _default_path(*parts: str) -> str:
    return os.path.join(os.path.expanduser("~"), *parts)


def _load_config_file(path: str) -> Dict[str, Any]:
    if not path or not os.path.exists(path):
        return {}

    _, ext = os.path.splitext(path.lower())
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if ext == ".json":
        return json.loads(content)
    if ext in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "YAML config file detected but PyYAML is not installed. "
                "Install PyYAML or use JSON config."
            ) from exc
        return yaml.safe_load(content) or {}

    raise ValueError(f"Unsupported config format: {ext}")


def load_config() -> Config:
    config_path = os.environ.get("MCP_CONFIG_FILE")
    file_config = _load_config_file(config_path) if config_path else {}

    client_secrets_file = os.environ.get(
        "GOOGLE_CLIENT_SECRETS_FILE",
        file_config.get("client_secrets_file", _default_path(".google", "oauth.keys.json")),
    )
    token_file = os.environ.get(
        "GOOGLE_TOKEN_FILE",
        file_config.get("token_file", _default_path(".google", "token.json")),
    )
    backup_dir = os.environ.get(
        "GOOGLE_BACKUP_DIR",
        file_config.get("backup_dir", _default_path(".google", "backups")),
    )
    log_file = os.environ.get(
        "GOOGLE_LOG_FILE",
        file_config.get("log_file", _default_path(".google", "mcp_operations.log")),
    )
    mcp_auth_token = os.environ.get("MCP_AUTH_TOKEN", file_config.get("mcp_auth_token"))

    scopes = file_config.get("scopes") or DEFAULT_SCOPES
    scopes = list(scopes)

    return Config(
        client_secrets_file=client_secrets_file,
        token_file=token_file,
        backup_dir=backup_dir,
        log_file=log_file,
        mcp_auth_token=mcp_auth_token,
        scopes=scopes,
    )
