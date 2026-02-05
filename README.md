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

## Smoke check
After the server is connected in your MCP client, call `get_gmail_profile()`.
If OAuth is configured, it should return the authenticated Gmail address.

## STDIO logging note
Do not write to stdout in STDIO servers. Use stderr or log to a file instead.

## Configuration
You can use a combined approach:
- ENV: `MCP_AUTH_TOKEN`, `GOOGLE_CLIENT_SECRETS_FILE`, `GOOGLE_TOKEN_FILE`,
  `GOOGLE_BACKUP_DIR`, `GOOGLE_LOG_FILE`, `MCP_CONFIG_FILE`.
- Config file: `client_secrets_file`, `token_file`, `backup_dir`, `log_file`, `scopes`.

If `MCP_CONFIG_FILE` is set, its values are used as defaults and ENV overrides them.

## Environment variables
Set environment variables in your shell or OS before starting the server.

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
- English: `docs/AUTH_SETUP.md`, `docs/TOOLS_REFERENCE.md`, `docs/SECURITY.md`, `docs/IDE_SETUP.md`
- Russian: `docs/ru/AUTH_SETUP.md`, `docs/ru/TOOLS_REFERENCE.md`, `docs/ru/SECURITY.md`, `docs/ru/IDE_SETUP.md`
