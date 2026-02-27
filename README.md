<div align="center">

# 🔧 MCP Google Tools Server

**A full-featured [Model Context Protocol](https://modelcontextprotocol.io) server for Google Workspace.**  
Give your AI assistant real-time access to Drive, Gmail, Calendar, Sheets, Docs, and Apps Script.

[![Python](https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-1.x-blueviolet?logo=anthropic&logoColor=white)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Google APIs](https://img.shields.io/badge/Google%20APIs-Drive%20%7C%20Gmail%20%7C%20Calendar%20%7C%20Sheets%20%7C%20Docs-red?logo=google)](https://developers.google.com)

[**English docs**](#documentation) · [**Документация на русском**](#документация)

</div>

---

## ✨ What it can do

| Service | Capabilities |
|---------|-------------|
| 📁 **Google Drive** | Search, copy, move, share, manage permissions |
| 📊 **Google Sheets** | Read/write ranges, named ranges, filter views, find & replace, CSV export |
| 📄 **Google Docs** | Read, create, append text, fill templates, export to PDF |
| 📧 **Gmail** | Draft, send, search, archive, label, delete with confirmation |
| 📅 **Google Calendar** | List events, find free slots, create meetings with attendees |
| ⚙️ **Apps Script** | Read, staged updates, auto-backup, rollback |
| 🔗 **Resources** | Attach live Drive / Gmail / Calendar / Sheets / Docs snapshots to AI context |
| 💬 **Prompts** | Ready-made AI templates: summarize inbox, analyze spreadsheet, plan week, search files |

---

## 🧩 MCP Primitives

This server exposes all three MCP primitive types:

<table>
<tr>
<td align="center" width="33%">

### 🛠 Tools
**50+ executable actions**<br/>
Called by the AI on demand.<br/>
Every tool is annotated with<br/>
`readOnlyHint` / `destructiveHint`<br/>
so clients can warn before risky actions.

</td>
<td align="center" width="33%">

### 📦 Resources
**Read-only data snapshots**<br/>
Attach live Google data directly<br/>
to the AI context window<br/>
without calling a tool.<br/>
Supports static URIs and templates.

</td>
<td align="center" width="33%">

### 💬 Prompts
**Reusable AI templates**<br/>
Select a prompt in your MCP client<br/>
to fetch live data and start<br/>
a structured conversation<br/>
in one click.

</td>
</tr>
</table>

---

## 🚀 Quick Start

### 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### 2 — Set up Google OAuth
Create an OAuth 2.0 Client ID in [Google Cloud Console](https://console.cloud.google.com/), download the JSON, and note its path.

> **Full step-by-step guide:** [docs/AUTH_SETUP.md](docs/AUTH_SETUP.md) · [docs/ru/AUTH_SETUP.md](docs/ru/AUTH_SETUP.md)

### 3 — Configure the server
```bash
cp config.example.yaml config.yaml
# then edit config.yaml — set paths and choose MCP_AUTH_TOKEN
```

<details>
<summary>💡 How to create <code>MCP_AUTH_TOKEN</code></summary>

`MCP_AUTH_TOKEN` is a secret string you choose. You can think of it as a **local activation key for this MCP server**, not as a network security layer or authentication mechanism.

- The server only checks that this token is configured before it starts handling tools — this is an extra safety step to avoid accidental runs without explicit setup.
- Invent any random string, e.g. `MySecretToken_2026!` or use a password generator.
- Recommended length: 16+ characters. Avoid reusing passwords.
- Set it in `config.yaml` → `mcp_auth_token: "your_token"` **or** as the env var `MCP_AUTH_TOKEN`.

The token is never sent anywhere — it is only checked locally inside the server process. It does **not** restrict what your AI agent can do once the server is running. For more details, see `docs/SECURITY.md` / `docs/ru/SECURITY.md`.

</details>

### 4 — Connect your IDE

Replace `<PROJECT_PATH>` with the absolute path to this repository and `your_token_here` with your token.

<details>
<summary><strong>Cursor</strong> — <code>.cursor/mcp.json</code> or <code>~/.cursor/mcp.json</code></summary>

```json
{
  "mcpServers": {
    "google-tools": {
      "command": "python",
      "args": ["<PROJECT_PATH>\\server.py"],
      "env": {
        "MCP_AUTH_TOKEN": "your_token_here",
        "MCP_CONFIG_FILE": "<PROJECT_PATH>\\config.yaml"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Windsurf</strong> — <code>%APPDATA%\Codeium\Windsurf\mcp_config.json</code> (Windows)</summary>

```json
{
  "mcpServers": {
    "google-tools": {
      "command": "python",
      "args": ["<PROJECT_PATH>\\server.py"],
      "env": {
        "MCP_AUTH_TOKEN": "your_token_here",
        "MCP_CONFIG_FILE": "<PROJECT_PATH>\\config.yaml"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>VS Code (Copilot MCP)</strong> — <code>.vscode/mcp.json</code> or <em>MCP: Open User Configuration</em></summary>

> Uses `servers` (not `mcpServers`). Requires VS Code 1.102+ and Copilot enabled.

```json
{
  "servers": {
    "google-tools": {
      "type": "stdio",
      "command": "python",
      "args": ["<PROJECT_PATH>\\server.py"],
      "env": {
        "MCP_AUTH_TOKEN": "your_token_here",
        "MCP_CONFIG_FILE": "<PROJECT_PATH>\\config.yaml"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Other IDEs</strong> — generic MCP stdio config</summary>

Use the same `command` / `args` / `env`. The root key may be `mcpServers` or `servers`.

```json
{
  "mcpServers": {
    "google-tools": {
      "command": "python",
      "args": ["<PROJECT_PATH>\\server.py"],
      "env": {
        "MCP_AUTH_TOKEN": "your_token_here",
        "MCP_CONFIG_FILE": "<PROJECT_PATH>\\config.yaml"
      }
    }
  }
}
```

</details>

### 5 — Smoke check
After connecting, call `get_gmail_profile()` in your AI client.  
It should return the authenticated Gmail address if OAuth is configured correctly.

---

## 📖 Usage Examples

<details>
<summary><strong>Basic operations</strong></summary>

```
# Verify authentication
Tool: get_gmail_profile
→ Authenticated Gmail address: user@example.com

# Search for files in Drive
Tool: find_files
Arguments: {"query": "name contains 'budget'"}
→ - Budget_2026.xlsx (ID: 1a2b3c...) [spreadsheet]

# Read a Google Sheet
Tool: read_sheet
Arguments: {"spreadsheet_id": "1a2b3c4d5e...", "range_name": "Sheet1!A1:C10"}
→ | Name | Email     | Status |
  | John | j@corp.io | Active |

# Create a draft email (safe by default — never sends without draft_mode=false)
Tool: send_email
Arguments: {"to": "colleague@example.com", "subject": "Notes", "body_text": "...", "draft_mode": true}
→ EMAIL DRAFT CREATED (ID: r1234...) — saved as draft, not sent.
```

</details>

<details>
<summary><strong>Resources — attach live data to context</strong></summary>

```
# Recent Drive files (no arguments needed)
Resource URI: gdrive://recent

# Unread inbox snapshot
Resource URI: gmail://inbox

# This week's calendar
Resource URI: gcalendar://upcoming

# Specific spreadsheet range
Resource URI: gsheets://1a2b3c4d5e.../Sheet1!A1:D20

# Specific Google Doc
Resource URI: gdocs://1a2b3c4d5e...
```

</details>

<details>
<summary><strong>Prompts — one-click AI workflows</strong></summary>

| Prompt | What it does |
|--------|-------------|
| `summarize_inbox` | Fetches recent Gmail messages → ready for AI summary |
| `analyze_spreadsheet` | Reads a sheet range → ready for AI analysis / charts |
| `plan_week` | Loads calendar events → ready for scheduling suggestions |
| `search_drive` | Searches Drive files → ready for organisation advice |

</details>

---

## 🛡 Safety Features

| Feature | Tools affected |
|---------|---------------|
| `confirm=true` required | `delete_email`, `gmail_archive`, `calendar_create_meeting`, `drive_revoke_public`, `doc_fill_template` |
| `dry_run=true` by default | `batch_delete_emails`, `sheet_find_replace` |
| Auto dry-run for large ranges | `clear_range` (prompts confirmation above threshold) |
| Draft mode by default | `send_email` (never sends unless `draft_mode=false`) |
| Public sharing blocked | `share_file` blocks `type=anyone` unless `allow_public=true` |
| Tool annotations | Every tool carries `readOnlyHint` / `destructiveHint` for client-side warnings |

> ⚠️ **Your AI agent has access to all data you authorize via OAuth.** Use read-only scopes for sensitive accounts. See [docs/SECURITY.md](docs/SECURITY.md).

---

## ⚙️ Configuration Reference

### `config.yaml` keys

| Key | Env override | Default | Description |
|-----|-------------|---------|-------------|
| `client_secrets_file` | `GOOGLE_CLIENT_SECRETS_FILE` | — | Path to OAuth JSON downloaded from Google Cloud |
| `token_file` | `GOOGLE_TOKEN_FILE` | `~/.google/token.json` | Where the OAuth token is saved after first login |
| `mcp_auth_token` | `MCP_AUTH_TOKEN` | — | **Required.** Token to activate the server |
| `log_file` | `GOOGLE_LOG_FILE` | stderr only | Path to a log file (optional) |
| `log_level` | `GOOGLE_LOG_LEVEL` | `INFO` | Log verbosity: `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `backup_dir` | `GOOGLE_BACKUP_DIR` | — | Directory for Apps Script auto-backups |
| `scopes` | — | full access | List of OAuth scopes (see security docs) |

> `MCP_CONFIG_FILE` — points to your `config.yaml`. Set this in the IDE `env` block.  
> Environment variables always override config file values.

<details>
<summary>Minimal <code>config.yaml</code> example</summary>

```yaml
client_secrets_file: "C:\\Users\\you\\.google\\oauth.keys.json"
token_file: "C:\\Users\\you\\.google\\token.json"
mcp_auth_token: "MySecretToken_2026!"
log_level: "INFO"
```

</details>

---

## 📦 Full Tool List

<details>
<summary>📁 Drive (8 tools)</summary>

| Tool | Type | Description |
|------|------|-------------|
| `find_files` | read | Search by name or Drive query |
| `drive_search_advanced` | read | Full Drive query syntax with result limit |
| `drive_list_permissions` | read | List file permissions |
| `create_folder` | write | Create a folder |
| `move_file` | write | Move a file to a folder |
| `drive_copy_file` | write | Copy a file |
| `share_file` | write | Share with user/group/domain/anyone |
| `drive_revoke_public` | destructive | Revoke public access (`confirm=true`) |

</details>

<details>
<summary>📊 Sheets (11 tools)</summary>

| Tool | Type | Description |
|------|------|-------------|
| `read_sheet` | read | Read a cell range |
| `get_spreadsheet_meta` | read | Spreadsheet metadata |
| `sheet_export_csv` | read | Export range to CSV |
| `append_row` | write | Append a row |
| `update_sheet` | write | Write rows to a range |
| `create_spreadsheet` | write | Create a new spreadsheet |
| `add_sheet` | write | Add a new tab/sheet |
| `sheet_create_filter_view` | write | Create a filter view |
| `sheet_create_named_range` | write | Create a named range |
| `sheet_find_replace` | write | Find & replace (`dry_run=true` by default) |
| `clear_range` | destructive | Clear a range (auto dry-run for large ranges) |

</details>

<details>
<summary>📄 Docs (5 tools)</summary>

| Tool | Type | Description |
|------|------|-------------|
| `read_doc` | read | Read document text |
| `doc_export_pdf` | read | Export document as binary PDF |
| `create_doc` | write | Create a new document |
| `append_to_doc` | write | Append text |
| `doc_fill_template` | destructive | Fill template placeholders (`confirm=true`) |

</details>

<details>
<summary>📧 Gmail (11 tools)</summary>

| Tool | Type | Description |
|------|------|-------------|
| `get_gmail_profile` | read | Get authenticated email address |
| `list_emails` | read | List emails (with optional search query) |
| `read_email` | read | Read a single email |
| `gmail_search_and_summarize` | read | Search and return brief summary |
| `create_draft` | write | Create a draft |
| `send_email` | write | Send or draft an email (`draft_mode=true` by default) |
| `send_draft` | write | Send an existing draft |
| `gmail_label_apply` | write | Apply a label (`dry_run=true` by default) |
| `gmail_archive` | write | Archive a message (`confirm=true`) |
| `delete_email` | destructive | Delete an email (`confirm=true`) |
| `batch_delete_emails` | destructive | Delete multiple emails (`dry_run=true` by default) |

</details>

<details>
<summary>📅 Calendar (4 tools)</summary>

| Tool | Type | Description |
|------|------|-------------|
| `list_events` | read | List upcoming events |
| `calendar_find_free_slots` | read | Find free time slots |
| `create_event` | write | Create an event |
| `calendar_create_meeting` | write | Create meeting with attendees (`confirm=true`) |

</details>

<details>
<summary>⚙️ Apps Script (6 tools)</summary>

| Tool | Type | Description |
|------|------|-------------|
| `get_script_content` | read | Read project files |
| `create_script_project` | write | Create a new project |
| `prepare_script_update` | write | Stage an update, get `operation_id` |
| `execute_operation` | write | Execute a staged update (with auto-backup) |
| `cancel_operation` | write | Cancel a pending staged update |
| `restore_script_backup` | write | Restore from auto-backup |

</details>

---

<a id="documentation"></a>
## 📚 Documentation

### 🇬🇧 English

| Document | Description |
|----------|-------------|
| [AUTH_SETUP.md](docs/AUTH_SETUP.md) | Step-by-step Google OAuth setup guide |
| [TOOLS_REFERENCE.md](docs/TOOLS_REFERENCE.md) | Full tools, resources, and prompts reference |
| [SECURITY.md](docs/SECURITY.md) | OAuth scopes, safety features, best practices |
| [IDE_SETUP.md](docs/IDE_SETUP.md) | Cursor, Windsurf, VS Code, and other IDE setup |
| [LEARN.md](LEARN.md) | How this MCP server was built (step-by-step tutorial) |

<a id="документация"></a>
### 🇷🇺 На русском

| Документ | Описание |
|----------|----------|
| [AUTH_SETUP.md](docs/ru/AUTH_SETUP.md) | Пошаговая настройка Google OAuth |
| [TOOLS_REFERENCE.md](docs/ru/TOOLS_REFERENCE.md) | Полный справочник инструментов, ресурсов и промптов |
| [SECURITY.md](docs/ru/SECURITY.md) | OAuth scopes, защиты, рекомендации |
| [IDE_SETUP.md](docs/ru/IDE_SETUP.md) | Настройка Cursor, Windsurf, VS Code и других IDE |

---

## ⚠️ Responsibility notice

You are responsible for understanding the risks and consequences of operations performed by this server.  
Use it at your own discretion and follow your organization's security policies.

---

<div align="center">

Built with ❤️ using [Model Context Protocol](https://modelcontextprotocol.io) · [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

</div>
