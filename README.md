# MCP Google Tools Server

MCP server for Google Drive, Sheets, Docs, Gmail, Calendar, and Apps Script.
The codebase is split into modules to make it easier to read, extend, and publish.

## Features
- Drive: search, move, copy, permissions.
- Sheets: read/write, clear ranges, find/replace, CSV export.
- Docs: read, create, template fill, PDF export.
- Gmail: drafts, send, search, delete with confirmation.
- Calendar: events, free slots, meetings with confirmation.
- Apps Script: read, staged updates with backup and rollback.

## Capabilities (full tool list)
- Drive: `find_files`, `create_folder`, `move_file`, `share_file`, `drive_search_advanced`,
  `drive_list_permissions`, `drive_revoke_public`, `drive_copy_file`.
- Sheets: `read_sheet`, `append_row`, `update_sheet`, `create_spreadsheet`, `add_sheet`,
  `clear_range`, `sheet_create_filter_view`, `sheet_export_csv`, `sheet_find_replace`,
  `sheet_create_named_range`, `get_spreadsheet_meta`.
- Docs: `read_doc`, `create_doc`, `append_to_doc`, `doc_fill_template`, `doc_export_pdf`.
- Gmail: `send_email`, `send_draft`, `get_gmail_profile`, `create_draft`, `list_emails`,
  `read_email`, `delete_email`, `batch_delete_emails`, `gmail_search_and_summarize`,
  `gmail_archive`, `gmail_label_apply`.
- Calendar: `list_events`, `create_event`, `calendar_find_free_slots`, `calendar_create_meeting`.
- Apps Script: `create_script_project`, `get_script_content`, `prepare_script_update`,
  `execute_operation`, `cancel_operation`, `restore_script_backup`.

## Security & Access Control

### Understanding OAuth Scopes
This server requests access to your Google account through OAuth scopes. Think of scopes as permission levels:

**Default configuration** (in `config.example.yaml`):
- Google Sheets: Read/write spreadsheets
- Google Drive: Full access to files and folders
- Google Docs: Read/write documents
- Gmail: Read, send, modify, and delete emails (`gmail.modify` includes read access)
- Google Calendar: Manage events and meetings
- Apps Script: Read and modify scripts and deployments

### Recommended Setup Approaches

**For testing and experimentation:**
- Create a **separate Google account** for testing
- Use the default scopes to explore all features
- This way, your personal/work data stays separate

**For production use:**
- Review and **limit scopes** to only what you need
- Example: If you only need to read sheets, use `auth/spreadsheets.readonly`
- See `docs/SECURITY.md` for scope customization guide

**For work accounts:**
- Check with your organization's IT/security policies first
- Consider using a service account with limited permissions
- Keep audit logs of MCP server actions

### Built-in Safety Features
The server includes safeguards to prevent accidents:
- **Confirmation required** for destructive operations (delete, archive)
- **Dry-run mode** for bulk operations (see examples below)
- **Draft mode** for emails (safe by default)
- **Public sharing blocked** unless explicitly allowed

**Your AI agent will have access to the data you authorize.** The `MCP_AUTH_TOKEN` is a server-side configuration check that ensures the operator has consciously enabled the server. It does not perform per-request client authentication. For STDIO-based MCP servers the transport is inherently local.

## Quick start
1) Install dependencies:
   - `pip install -r requirements.txt`

2) Configure OAuth:
   - Create an OAuth Client ID in Google Cloud Console.
   - Download `oauth.keys.json` and place it in a convenient path.
   - See: `docs/AUTH_SETUP.md`.

3) Configure the server:
   - Copy `config.example.yaml` to `config.yaml`.
   - Set paths and `MCP_AUTH_TOKEN`.

4) Run the server:
   - `python server.py`

**IDE setup:** Use one of two ways to run the server. Replace `<PROJECT_PATH>` and `your_token_here` in the blocks below.

| Option | Command | Notes |
|--------|---------|-------|
| **A (recommended)** | `uv run` | No pre-installed deps. Install [uv](https://docs.astral.sh/uv/): `pip install uv` or `winget install astral-sh.uv` |
| **B** | `python` | Requires `pip install -r requirements.txt`. IDE must use the same Python (e.g. project venv). If you get `ModuleNotFoundError: No module named 'yaml'`, use Option A |

<details>
<summary><strong>Cursor</strong> — <code>.cursor/mcp.json</code> or <code>~/.cursor/mcp.json</code></summary>

**Option A — uv run:**
```json
{
  "mcpServers": {
    "google-tools": {
      "command": "uv",
      "args": [
        "run",
        "--with", "google-api-python-client",
        "--with", "PyYAML",
        "--with", "google-auth",
        "--with", "google-auth-oauthlib",
        "--with", "mcp",
        "<PROJECT_PATH>\\\\server.py"
      ],
      "env": {
        "MCP_AUTH_TOKEN": "your_token_here",
        "MCP_CONFIG_FILE": "<PROJECT_PATH>\\\\config.yaml"
      }
    }
  }
}
```

**Option B — python:**
```json
{
  "mcpServers": {
    "google-tools": {
      "command": "python",
      "args": ["<PROJECT_PATH>\\\\server.py"],
      "env": {
        "MCP_AUTH_TOKEN": "your_token_here",
        "MCP_CONFIG_FILE": "<PROJECT_PATH>\\\\config.yaml"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Windsurf</strong> — <code>%APPDATA%\Codeium\Windsurf\mcp_config.json</code> (Windows)</summary>

**Option A — uv run:**
```json
{
  "mcpServers": {
    "google-tools": {
      "command": "uv",
      "args": [
        "run",
        "--with", "google-api-python-client",
        "--with", "PyYAML",
        "--with", "google-auth",
        "--with", "google-auth-oauthlib",
        "--with", "mcp",
        "<PROJECT_PATH>\\\\server.py"
      ],
      "env": {
        "MCP_AUTH_TOKEN": "your_token_here",
        "MCP_CONFIG_FILE": "<PROJECT_PATH>\\\\config.yaml"
      }
    }
  }
}
```

**Option B — python:**
```json
{
  "mcpServers": {
    "google-tools": {
      "command": "python",
      "args": ["<PROJECT_PATH>\\\\server.py"],
      "env": {
        "MCP_AUTH_TOKEN": "your_token_here",
        "MCP_CONFIG_FILE": "<PROJECT_PATH>\\\\config.yaml"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>VS Code (Copilot MCP)</strong> — <code>.vscode/mcp.json</code> or MCP: Open User Configuration</summary>

> Uses `servers`, not `mcpServers`. Requires VS Code 1.102+ and Copilot enabled.

**Option A — uv run:**
```json
{
  "servers": {
    "google-tools": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "--with", "google-api-python-client",
        "--with", "PyYAML",
        "--with", "google-auth",
        "--with", "google-auth-oauthlib",
        "--with", "mcp",
        "<PROJECT_PATH>\\\\server.py"
      ],
      "env": {
        "MCP_AUTH_TOKEN": "your_token_here",
        "MCP_CONFIG_FILE": "<PROJECT_PATH>\\\\config.yaml"
      }
    }
  }
}
```

**Option B — python:**
```json
{
  "servers": {
    "google-tools": {
      "type": "stdio",
      "command": "python",
      "args": ["<PROJECT_PATH>\\\\server.py"],
      "env": {
        "MCP_AUTH_TOKEN": "your_token_here",
        "MCP_CONFIG_FILE": "<PROJECT_PATH>\\\\config.yaml"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Other IDEs</strong> — generic MCP config</summary>

Use the same `command` / `args` / `env`. Root key may be `mcpServers` or `servers`.

**Option A — uv run:**
```json
{
  "mcpServers": {
    "google-tools": {
      "command": "uv",
      "args": [
        "run",
        "--with", "google-api-python-client",
        "--with", "PyYAML",
        "--with", "google-auth",
        "--with", "google-auth-oauthlib",
        "--with", "mcp",
        "<PROJECT_PATH>\\\\server.py"
      ],
      "env": {
        "MCP_AUTH_TOKEN": "your_token_here",
        "MCP_CONFIG_FILE": "<PROJECT_PATH>\\\\config.yaml"
      }
    }
  }
}
```

**Option B — python:**
```json
{
  "mcpServers": {
    "google-tools": {
      "command": "python",
      "args": ["<PROJECT_PATH>\\\\server.py"],
      "env": {
        "MCP_AUTH_TOKEN": "your_token_here",
        "MCP_CONFIG_FILE": "<PROJECT_PATH>\\\\config.yaml"
      }
    }
  }
}
```

</details>

## Smoke check
After the server is connected in your MCP client, call `get_gmail_profile()`.
If OAuth is configured, it should return the authenticated Gmail address.

## Usage examples

### Basic operations
```
# Get your Gmail address (smoke test)
Tool: get_gmail_profile
Result: Authenticated Gmail address: user@example.com

# Search for files in Drive
Tool: find_files
Arguments: {"query": "name contains 'budget'"}
Result: Found files:
- Budget_2026.xlsx (ID: 1a2b3c...) [application/vnd.google-apps.spreadsheet]

# Read a Google Sheet
Tool: read_sheet
Arguments: {
  "spreadsheet_id": "1a2b3c4d5e...",
  "range_name": "Sheet1!A1:C10"
}
Result: Data from sheet (range Sheet1!A1:C10):
| Name | Email | Status |
| John | john@example.com | Active |
...

# Create a draft email (safe by default)
Tool: send_email
Arguments: {
  "to": "colleague@example.com",
  "subject": "Meeting notes",
  "body_text": "Here are the notes from our meeting...",
  "draft_mode": true
}
Result: EMAIL DRAFT CREATED (ID: r1234...)
Email saved as DRAFT, not sent yet.
To send: send_email(..., draft_mode=False)
```

### Safety features
```
# Destructive operations require confirmation
Tool: delete_email
Arguments: {"message_id": "18abc...", "confirm": false}
Result: CONFIRMATION REQUIRED
This will permanently delete email 18abc...
To proceed, call this tool again with confirm=True

# Large operations use dry-run mode
Tool: clear_range
Arguments: {"spreadsheet_id": "1a2b...", "range_name": "Sheet1!A1:Z1000"}
Result: DRY RUN: Large range detected (26,000 cells)
Would clear range: Sheet1!A1:Z1000
To proceed: clear_range(..., confirm=True)
```

## STDIO logging note
The server logs to stderr (not stdout) so it never interferes with the
STDIO MCP transport. If a `log_file` is configured, logs are also written to that file.

## Configuration
You can use a combined approach:
- ENV: `MCP_AUTH_TOKEN`, `GOOGLE_CLIENT_SECRETS_FILE`, `GOOGLE_TOKEN_FILE`,
  `GOOGLE_BACKUP_DIR`, `GOOGLE_LOG_FILE`, `MCP_CONFIG_FILE`.
- Config file: `client_secrets_file`, `token_file`, `backup_dir`, `log_file`, `scopes`.

If `MCP_CONFIG_FILE` is set, its values are used as defaults and ENV overrides them.

## Environment variables
Set environment variables in your shell or OS before starting the server,
or pass them in the `env` block of your IDE's MCP config (see `docs/IDE_SETUP.md`).

Windows PowerShell:
- `setx MCP_AUTH_TOKEN "your_token"`
- `setx MCP_CONFIG_FILE "D:\path\to\config.yaml"`
- `setx GOOGLE_CLIENT_SECRETS_FILE "D:\path\to\oauth.keys.json"`

macOS/Linux (bash/zsh):
- `export MCP_AUTH_TOKEN="your_token"`
- `export MCP_CONFIG_FILE="/path/to/config.yaml"`
- `export GOOGLE_CLIENT_SECRETS_FILE="/path/to/oauth.keys.json"`

## Safety and responsibility
Some operations require confirmation or run in dry-run mode:
- Deleting emails, archiving, making files public.
- Clearing large ranges in Sheets.
See: `docs/SECURITY.md`.

You are responsible for understanding the risks and the consequences of actions
performed by this server. Use it at your own discretion and follow your
organization's security policies.

## Documentation
- [LEARN.md](LEARN.md) — Step-by-step guide to building an MCP server like this one
- English: `docs/AUTH_SETUP.md`, `docs/TOOLS_REFERENCE.md`, `docs/SECURITY.md`, `docs/IDE_SETUP.md`
- Russian: `docs/ru/AUTH_SETUP.md`, `docs/ru/TOOLS_REFERENCE.md`, `docs/ru/SECURITY.md`, `docs/ru/IDE_SETUP.md`
