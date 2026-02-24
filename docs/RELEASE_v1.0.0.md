# Release v1.0.0

First release with full MCP spec compliance.

## Highlights

- **Resources**: `list_resources` / `read_resource` for Drive, Gmail, Calendar, Sheets, Docs (`gdrive://`, `gmail://`, `gcalendar://`, `gsheets://`, `gdocs://`)
- **Prompts**: `list_prompts` / `get_prompt` with `summarize_inbox`, `analyze_spreadsheet`, `plan_week`, `search_drive`
- **Tool annotations**: `readOnlyHint` / `destructiveHint` on all 50+ tools for client-side safety
- **Error handling**: `isError=True` in tool error responses per MCP spec
- **Binary PDF**: `doc_export_pdf` returns `EmbeddedResource` (`BlobResourceContents`) instead of base64 text
- **Config**: config/logger init moved into `run()`; configurable log level (`GOOGLE_LOG_LEVEL`)
- **Dependencies**: `mcp` pinned to `>=1.0.0,<2`

## Install

```bash
pip install -r requirements.txt
# or from repo
pip install .
```

## Documentation

- [README](../README.md)
- [AUTH_SETUP](AUTH_SETUP.md) · [TOOLS_REFERENCE](TOOLS_REFERENCE.md) · [SECURITY](SECURITY.md) · [IDE_SETUP](IDE_SETUP.md)
- [Russian docs](ru/)
