# LEARN: Build an MCP Google Tools Server

This document breaks the project into small components and walks through each stage so you can build your own MCP server that exposes Google APIs to AI assistants.

---

## What We're Building

An **MCP (Model Context Protocol) server** that:
- Runs as a STDIO process (stdin/stdout) launched by your IDE
- Exposes tools (Drive, Sheets, Gmail, Calendar, etc.) to the AI
- Uses OAuth 2.0 for Google API access
- Applies safety patterns (confirm, dry-run) for destructive operations

---

## Prerequisites

- Python 3.10+
- A Google Cloud project with OAuth credentials
- An IDE that supports MCP (Cursor, Windsurf, VS Code with Copilot)

---

## Part 1: Project Structure

```
my-mcp-google/
├── server.py           # Entry point, runs the MCP server
├── config.example.yaml # Example configuration
├── requirements.txt
├── mcp_google/
│   ├── __init__.py
│   ├── config.py       # Load config from file + env
│   ├── auth.py         # OAuth flow and credentials
│   ├── logging.py      # stderr + optional file logging
│   ├── security.py     # Token check, validation helpers
│   ├── operations.py   # Shared utilities (backups, etc.)
│   ├── server.py       # MCP Server, tool registration
│   └── handlers/       # One module per Google API
│       ├── drive.py
│       ├── sheets.py
│       ├── gmail.py
│       └── ...
├── docs/               # User-facing docs
│   ├── AUTH_SETUP.md
│   ├── IDE_SETUP.md
│   ├── SECURITY.md
│   └── TOOLS_REFERENCE.md
```

**Step 1.1:** Create the directory structure and a minimal `requirements.txt`:

```
mcp>=1.0.0
google-api-python-client>=2.100.0,<3
google-auth-oauthlib>=1.2.0
PyYAML>=6.0
```

---

## Part 2: Configuration Layer

The server needs paths (OAuth secrets, token file) and an auth token. We load from:
1. YAML/JSON file (via `MCP_CONFIG_FILE`)
2. Environment variables (override file values)

**Step 2.1:** Implement `config.py`:

```python
# mcp_google/config.py
import os
from dataclasses import dataclass
from typing import List, Optional

@dataclass(frozen=True)
class Config:
    client_secrets_file: str
    token_file: str
    mcp_auth_token: Optional[str]
    scopes: List[str]

def load_config() -> Config:
    config_path = os.environ.get("MCP_CONFIG_FILE")
    file_config = _load_yaml(config_path) if config_path else {}
    
    return Config(
        client_secrets_file=os.environ.get(
            "GOOGLE_CLIENT_SECRETS_FILE",
            file_config.get("client_secrets_file", "~/.google/oauth.keys.json")
        ),
        token_file=os.environ.get(
            "GOOGLE_TOKEN_FILE",
            file_config.get("token_file", "~/.google/token.json")
        ),
        mcp_auth_token=os.environ.get("MCP_AUTH_TOKEN", file_config.get("mcp_auth_token")),
        scopes=file_config.get("scopes") or DEFAULT_SCOPES,
    )
```

**Step 2.2:** Create `config.example.yaml`:

```yaml
client_secrets_file: "C:\\Users\\you\\.google\\oauth.keys.json"
token_file: "C:\\Users\\you\\.google\\token.json"
mcp_auth_token: "change_me"

scopes:
  - "https://www.googleapis.com/auth/spreadsheets"
  - "https://www.googleapis.com/auth/gmail.modify"
```

See `config.example.yaml` in this repo for the full default scopes.

---

## Part 3: OAuth Setup

The server uses the Installed Application flow: user authorizes in a browser, token is saved locally.

**Step 3.1:** Follow [docs/AUTH_SETUP.md](docs/AUTH_SETUP.md):

1. Open [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable APIs (Drive, Sheets, Gmail, etc.)
3. Create OAuth Client ID (Desktop app)
4. Download JSON → save as `oauth.keys.json`

**Step 3.2:** Implement `auth.py`:

```python
# mcp_google/auth.py
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def get_creds(config: Config) -> Credentials:
    creds = None
    if os.path.exists(config.token_file):
        creds = Credentials.from_authorized_user_file(config.token_file, config.scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.client_secrets_file, config.scopes
            )
            creds = flow.run_local_server(port=0)
        with open(config.token_file, "w") as f:
            f.write(creds.to_json())
    return creds
```

On first run, a browser window opens for authorization.

---

## Part 4: MCP Server Skeleton

MCP servers communicate via JSON-RPC over STDIO. The `mcp` Python package provides the transport.

**Step 4.1:** Entry point `server.py`:

```python
# server.py (project root)
import asyncio
from mcp_google.server import run

if __name__ == "__main__":
    asyncio.run(run())
```

**Step 4.2:** Core server in `mcp_google/server.py`:

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

config = load_config()
server = Server("My Google Tools")

async def run() -> None:
    async with stdio_server() as (read, write):
        await server.run(
            read_stream=read,
            write_stream=write,
            initialization_options=server.create_initialization_options(),
        )
```

> **Important:** MCP uses stdout for JSON-RPC. Log only to stderr or a file. See `mcp_google/logging.py` for `StreamHandler(sys.stderr)`.

---

## Part 5: Registering Tools

Tools are declared with `name`, `description`, and `inputSchema` (JSON Schema).

**Step 5.1:** Decorate `handle_list_tools`:

```python
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_gmail_profile",
            description="Get the authenticated Gmail address",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="read_sheet",
            description="Read data from a Google Sheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "range_name": {"type": "string"},
                },
                "required": ["spreadsheet_id", "range_name"],
            },
        ),
    ]
```

**Step 5.2:** Implement `handle_call_tool`:

```python
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list:
    if not arguments:
        arguments = {}
    
    require_token_configured(config.mcp_auth_token)  # config check
    
    handlers = {
        "get_gmail_profile": lambda a: get_gmail_profile_handler(config, logger),
        "read_sheet": lambda a: read_sheet_handler(
            config, logger, a.get("spreadsheet_id"), a.get("range_name")
        ),
    }
    
    if name not in handlers:
        raise ValueError(f"Unknown tool: {name}")
    
    result = await asyncio.to_thread(handlers[name], arguments)
    return [types.TextContent(type="text", text=str(result))]
```

> Use `asyncio.to_thread()` because Google API calls are synchronous and would block the event loop.

---

## Part 6: Implementing Handlers

Handlers are plain functions that return strings. They call Google APIs via `google-api-python-client`.

**Step 6.1:** Minimal Gmail handler:

```python
# mcp_google/handlers/gmail.py
from googleapiclient.discovery import build

def get_gmail_profile_handler(config: Config, logger: logging.Logger) -> str:
    creds = get_creds(config)
    service = build("gmail", "v1", credentials=creds)
    profile = service.users().getProfile(userId="me").execute()
    return f"Authenticated Gmail: {profile.get('emailAddress')}"
```

**Step 6.2:** Sheets handler:

```python
# mcp_google/handlers/sheets.py
def read_sheet_handler(config: Config, logger: logging.Logger,
                       spreadsheet_id: str, range_name: str) -> str:
    creds = get_creds(config)
    service = build("sheets", "v4", credentials=creds)
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name
    ).execute()
    values = result.get("values", [])
    return "\n".join(" | ".join(row) for row in values)
```

Split handlers by domain (Drive, Sheets, Gmail, Calendar, Docs, Apps Script) and import them in `handlers/__init__.py`. See `mcp_google/handlers/` in this repo for full implementations.

---

## Part 7: Safety Patterns

Destructive or bulk operations should require explicit confirmation or run in dry-run mode first.

**Pattern A — `confirm` flag:**

```python
def delete_email_handler(..., confirm: bool = False) -> str:
    if not confirm:
        return "CONFIRMATION REQUIRED. Call again with confirm=True"
    # perform delete
```

**Pattern B — dry-run:**

```python
def batch_delete_emails_handler(..., dry_run: bool = True) -> str:
    if dry_run:
        return f"DRY RUN: Would delete {len(ids)} emails. Set dry_run=False to proceed."
    # perform delete
```

**Pattern C — large range check:**

```python
if total_cells > 100 and not confirm:
    return "Large range detected. Call with confirm=True to clear."
```

See [docs/SECURITY.md](docs/SECURITY.md) for the full list of safeguards and OAuth scope customization.

---

## Part 8: IDE Integration

The IDE launches your server as a subprocess and passes env vars. Add an MCP config entry.

**For Cursor**, edit `.cursor/mcp.json` (or global `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "google-tools": {
      "command": "python",
      "args": ["D:\\path\\to\\your\\project\\server.py"],
      "env": {
        "MCP_AUTH_TOKEN": "your_token",
        "MCP_CONFIG_FILE": "D:\\path\\to\\your\\project\\config.yaml"
      }
    }
  }
}
```

**For Windsurf and VS Code**, see [docs/IDE_SETUP.md](docs/IDE_SETUP.md).

---

## Part 9: Smoke Test and Usage

1. Run locally: `python server.py` (it will wait on stdin).
2. Connect via IDE (restart IDE or reload MCP config).
3. Call `get_gmail_profile()` — if OAuth is configured, you get your Gmail address.

Full tool reference and examples: [docs/TOOLS_REFERENCE.md](docs/TOOLS_REFERENCE.md).

---

## Summary: From Zero to Working Server

| Step | What to do |
|------|------------|
| 1 | Create project layout, `requirements.txt` |
| 2 | Implement `config.py`, `config.example.yaml` |
| 3 | Set up OAuth in Google Cloud, implement `auth.py` |
| 4 | Add MCP skeleton (`server.py`, stdio transport) |
| 5 | Register tools with `@server.list_tools()` and `inputSchema` |
| 6 | Implement handlers (Gmail, Sheets, Drive, etc.) |
| 7 | Add `confirm` / dry-run for destructive ops |
| 8 | Add IDE MCP config (Cursor, Windsurf, VS Code) |
| 9 | Smoke test with `get_gmail_profile()` |

---

## Further Reading

- [docs/AUTH_SETUP.md](docs/AUTH_SETUP.md) — OAuth setup
- [docs/IDE_SETUP.md](docs/IDE_SETUP.md) — IDE MCP config
- [docs/SECURITY.md](docs/SECURITY.md) — Scopes and safeguards
- [docs/TOOLS_REFERENCE.md](docs/TOOLS_REFERENCE.md) — All tools and examples

[MCP Specification](https://spec.modelcontextprotocol.io/) — Protocol details.
