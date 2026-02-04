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

## Quick start
1) Install dependencies:
   - `pip install -r requirements.txt`
   - MCP runtime/SDK: install the one required by your IDE/runtime

2) Configure OAuth:
   - Create an OAuth Client ID in Google Cloud Console.
   - Download `oauth.keys.json` and place it in a convenient path.
   - See: `docs/AUTH_SETUP.md`.

3) Configure the server:
   - Copy `.env.example` → `.env`.
   - Copy `config.example.yaml` → `config.yaml`.
   - Set paths and `MCP_AUTH_TOKEN`.

4) Run the server:
   - `python server.py`

## Configuration
You can use a combined approach:
- ENV: `MCP_AUTH_TOKEN`, `GOOGLE_CLIENT_SECRETS_FILE`, `GOOGLE_TOKEN_FILE`,
  `GOOGLE_BACKUP_DIR`, `GOOGLE_LOG_FILE`, `MCP_CONFIG_FILE`.
- Config file: `client_secrets_file`, `token_file`, `backup_dir`, `log_file`, `scopes`.

If `MCP_CONFIG_FILE` is set, its values are used as defaults and ENV overrides them.

## Safety and responsibility
Some operations require confirmation or run in dry-run mode:
- Deleting emails, archiving, making files public.
- Clearing large ranges in Sheets.
See: `docs/SECURITY.md`.

You are responsible for understanding the risks and the consequences of actions
performed by this server. Use it at your own discretion and follow your
organization's security policies.

## Documentation
- English: `docs/AUTH_SETUP.md`, `docs/TOOLS_REFERENCE.md`, `docs/SECURITY.md`, `docs/IDE_SETUP.md`
- Russian: `docs/ru/AUTH_SETUP.md`, `docs/ru/TOOLS_REFERENCE.md`, `docs/ru/SECURITY.md`, `docs/ru/IDE_SETUP.md`
