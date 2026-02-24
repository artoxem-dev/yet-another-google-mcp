"""MCP server exposing Google Workspace tools, resources and prompts."""

import asyncio
import base64
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from typing import List

from pydantic import AnyUrl

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.lowlevel.helper_types import ReadResourceContents
import mcp.types as types

from .config import load_config
from .logging import setup_logging
from .security import require_token_configured
from .operations import BinaryResult
from .handlers import (
    add_sheet_handler,
    append_row_handler,
    append_to_doc_handler,
    batch_delete_emails_handler,
    calendar_create_meeting_handler,
    calendar_find_free_slots_handler,
    cancel_operation_handler,
    clear_range_handler,
    create_doc_handler,
    create_draft_handler,
    create_event_handler,
    create_folder_handler,
    create_script_project_handler,
    create_spreadsheet_handler,
    delete_email_handler,
    doc_export_pdf_handler,
    doc_fill_template_handler,
    drive_copy_file_handler,
    drive_list_permissions_handler,
    drive_revoke_public_handler,
    drive_search_advanced_handler,
    execute_operation_handler,
    find_files_handler,
    get_gmail_profile_handler,
    get_script_content_handler,
    get_spreadsheet_meta_handler,
    gmail_archive_handler,
    gmail_label_apply_handler,
    gmail_search_and_summarize_handler,
    list_emails_handler,
    list_events_handler,
    move_file_handler,
    prepare_script_update_handler,
    read_doc_handler,
    read_email_handler,
    read_sheet_handler,
    restore_script_backup_handler,
    send_draft_handler,
    send_email_handler,
    share_file_handler,
    sheet_create_filter_view_handler,
    sheet_create_named_range_handler,
    sheet_export_csv_handler,
    sheet_find_replace_handler,
    update_sheet_handler,
)

# ---------------------------------------------------------------------------
# Annotation presets (reused across tool definitions)
# ---------------------------------------------------------------------------
_READ_ONLY = types.ToolAnnotations(readOnlyHint=True, destructiveHint=False)
_WRITE = types.ToolAnnotations(readOnlyHint=False, destructiveHint=False)
_DESTRUCTIVE = types.ToolAnnotations(readOnlyHint=False, destructiveHint=True)


def _tools() -> List[types.Tool]:
    """Return the full list of tool definitions with annotations."""
    return [
        # ── Google Drive ──────────────────────────────────────────────────
        types.Tool(
            name="find_files",
            description="Search for files on Google Drive. Query example: 'name contains \"System\"'",
            inputSchema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            annotations=_READ_ONLY,
        ),
        types.Tool(
            name="drive_search_advanced",
            description="Advanced Google Drive search with full query syntax",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 50},
                },
                "required": ["query"],
            },
            annotations=_READ_ONLY,
        ),
        types.Tool(
            name="drive_list_permissions",
            description="List permissions for a Drive file",
            inputSchema={
                "type": "object",
                "properties": {"file_id": {"type": "string"}},
                "required": ["file_id"],
            },
            annotations=_READ_ONLY,
        ),
        types.Tool(
            name="create_folder",
            description="Create a folder in Google Drive",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "parent_id": {"type": "string"},
                },
                "required": ["name"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="move_file",
            description="Move a file to a different folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {"type": "string"},
                    "folder_id": {"type": "string"},
                },
                "required": ["file_id", "folder_id"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="drive_copy_file",
            description="Copy a Drive file to a new file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {"type": "string"},
                    "name": {"type": "string"},
                    "parent_id": {"type": "string"},
                },
                "required": ["file_id"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="share_file",
            description=(
                "Share a file with a user or make it public. "
                "REQUIRES allow_public=True to share publicly!"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {"type": "string"},
                    "role": {
                        "type": "string",
                        "enum": ["reader", "commenter", "writer"],
                    },
                    "type": {
                        "type": "string",
                        "enum": ["user", "group", "domain", "anyone"],
                        "description": "Access type. 'anyone' requires allow_public=True",
                    },
                    "email_address": {
                        "type": "string",
                        "description": "Required for type 'user' or 'group'",
                    },
                    "allow_public": {
                        "type": "boolean",
                        "description": "MUST be true to share with type='anyone'. Security check.",
                        "default": False,
                    },
                },
                "required": ["file_id", "role"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="drive_revoke_public",
            description="Revoke public access (type=anyone) for a Drive file. Requires confirm=True.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {"type": "string"},
                    "confirm": {"type": "boolean", "default": False},
                },
                "required": ["file_id"],
            },
            annotations=_DESTRUCTIVE,
        ),
        # ── Google Sheets ─────────────────────────────────────────────────
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
            annotations=_READ_ONLY,
        ),
        types.Tool(
            name="get_spreadsheet_meta",
            description="Get metadata (sheets, titles) of a spreadsheet",
            inputSchema={
                "type": "object",
                "properties": {"spreadsheet_id": {"type": "string"}},
                "required": ["spreadsheet_id"],
            },
            annotations=_READ_ONLY,
        ),
        types.Tool(
            name="sheet_export_csv",
            description="Export a range as CSV text",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "range_name": {"type": "string"},
                    "max_rows": {"type": "integer", "default": 5000},
                },
                "required": ["spreadsheet_id", "range_name"],
            },
            annotations=_READ_ONLY,
        ),
        types.Tool(
            name="create_spreadsheet",
            description="Create a new Google Spreadsheet",
            inputSchema={
                "type": "object",
                "properties": {"title": {"type": "string"}},
                "required": ["title"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="add_sheet",
            description="Add a new sheet (tab) to a spreadsheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "title": {"type": "string"},
                },
                "required": ["spreadsheet_id", "title"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="append_row",
            description="Append a row to a Google Sheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "range_name": {"type": "string"},
                    "values": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["spreadsheet_id", "range_name", "values"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="update_sheet",
            description="Update data in a Google Sheet. 'values' must be a list of lists of strings (rows of columns).",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "range_name": {"type": "string"},
                    "values": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "required": ["spreadsheet_id", "range_name", "values"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="clear_range",
            description="Clear values in a spreadsheet range. Auto dry-run for large ranges (>100 cells).",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "range_name": {"type": "string"},
                    "confirm": {
                        "type": "boolean",
                        "description": "Must be true to clear large ranges (>100 cells)",
                        "default": False,
                    },
                },
                "required": ["spreadsheet_id", "range_name"],
            },
            annotations=_DESTRUCTIVE,
        ),
        types.Tool(
            name="sheet_find_replace",
            description="Find/replace in a range with dry-run preview",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "range_name": {"type": "string"},
                    "find_text": {"type": "string"},
                    "replace_text": {"type": "string"},
                    "dry_run": {"type": "boolean", "default": True},
                    "match_case": {"type": "boolean", "default": False},
                },
                "required": ["spreadsheet_id", "range_name", "find_text", "replace_text"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="sheet_create_filter_view",
            description="Create a filter view for a sheet with grid range",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "sheet_id": {"type": "integer"},
                    "title": {"type": "string"},
                    "start_row": {"type": "integer", "default": 0},
                    "end_row": {"type": "integer"},
                    "start_col": {"type": "integer", "default": 0},
                    "end_col": {"type": "integer"},
                },
                "required": ["spreadsheet_id", "sheet_id", "title"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="sheet_create_named_range",
            description="Create a named range using grid indexes",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "name": {"type": "string"},
                    "sheet_id": {"type": "integer"},
                    "start_row": {"type": "integer"},
                    "end_row": {"type": "integer"},
                    "start_col": {"type": "integer"},
                    "end_col": {"type": "integer"},
                },
                "required": [
                    "spreadsheet_id",
                    "name",
                    "sheet_id",
                    "start_row",
                    "end_row",
                    "start_col",
                    "end_col",
                ],
            },
            annotations=_WRITE,
        ),
        # ── Google Docs ───────────────────────────────────────────────────
        types.Tool(
            name="read_doc",
            description="Read the content of a Google Doc",
            inputSchema={
                "type": "object",
                "properties": {"document_id": {"type": "string"}},
                "required": ["document_id"],
            },
            annotations=_READ_ONLY,
        ),
        types.Tool(
            name="create_doc",
            description="Create a new Google Doc",
            inputSchema={
                "type": "object",
                "properties": {"title": {"type": "string"}},
                "required": ["title"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="append_to_doc",
            description="Append text to a Google Doc",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string"},
                    "text": {"type": "string"},
                },
                "required": ["document_id", "text"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="doc_fill_template",
            description="Fill a Google Doc template by replacing placeholders. Requires confirm=True.",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string"},
                    "replacements": {"type": "object"},
                    "confirm": {"type": "boolean", "default": False},
                },
                "required": ["document_id", "replacements"],
            },
            annotations=_DESTRUCTIVE,
        ),
        types.Tool(
            name="doc_export_pdf",
            description="Export a Google Doc to PDF and return it as binary (EmbeddedResource)",
            inputSchema={
                "type": "object",
                "properties": {"document_id": {"type": "string"}},
                "required": ["document_id"],
            },
            annotations=_READ_ONLY,
        ),
        # ── Apps Script ───────────────────────────────────────────────────
        types.Tool(
            name="create_script_project",
            description="Create a new Google Apps Script project",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "parent_id": {"type": "string"},
                },
                "required": ["title"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="get_script_content",
            description="Get the content of a Google Apps Script project",
            inputSchema={
                "type": "object",
                "properties": {"script_id": {"type": "string"}},
                "required": ["script_id"],
            },
            annotations=_READ_ONLY,
        ),
        types.Tool(
            name="prepare_script_update",
            description="STEP 1: Prepare a Google Apps Script update with automatic backup. Returns operation_id.",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_id": {
                        "type": "string",
                        "description": "The Apps Script project ID",
                    },
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "source": {"type": "string"},
                            },
                            "required": ["name", "type", "source"],
                        },
                        "description": "Array of files to update",
                    },
                },
                "required": ["script_id", "files"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="execute_operation",
            description="STEP 2: Execute a prepared operation by operation_id (from prepare_script_update)",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation_id": {
                        "type": "string",
                        "description": "The operation ID from prepare_script_update",
                    }
                },
                "required": ["operation_id"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="cancel_operation",
            description="Cancel a prepared operation before execution",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation_id": {
                        "type": "string",
                        "description": "The operation ID to cancel",
                    }
                },
                "required": ["operation_id"],
            },
            annotations=types.ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True),
        ),
        types.Tool(
            name="restore_script_backup",
            description="Restore a script from a backup file",
            inputSchema={
                "type": "object",
                "properties": {
                    "backup_path": {
                        "type": "string",
                        "description": "Full path to the backup JSON file",
                    }
                },
                "required": ["backup_path"],
            },
            annotations=_WRITE,
        ),
        # ── Gmail ─────────────────────────────────────────────────────────
        types.Tool(
            name="get_gmail_profile",
            description="Get the authenticated Gmail address for the current OAuth token",
            inputSchema={"type": "object", "properties": {}, "required": []},
            annotations=_READ_ONLY,
        ),
        types.Tool(
            name="list_emails",
            description="List emails from Gmail",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {"type": "integer"},
                    "query": {
                        "type": "string",
                        "description": "Gmail search query (e.g. 'is:unread')",
                    },
                },
                "required": [],
            },
            annotations=_READ_ONLY,
        ),
        types.Tool(
            name="read_email",
            description="Read a specific email by ID",
            inputSchema={
                "type": "object",
                "properties": {"message_id": {"type": "string"}},
                "required": ["message_id"],
            },
            annotations=_READ_ONLY,
        ),
        types.Tool(
            name="gmail_search_and_summarize",
            description="Search Gmail and return a brief summary",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 50},
                },
                "required": ["query"],
            },
            annotations=_READ_ONLY,
        ),
        types.Tool(
            name="create_draft",
            description="Create a draft email in Gmail",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body_text": {"type": "string"},
                },
                "required": ["to", "subject", "body_text"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="send_email",
            description="Send an email via Gmail. Defaults to draft_mode=True for safety!",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string"},
                    "body_text": {"type": "string"},
                    "draft_mode": {
                        "type": "boolean",
                        "description": "If true (default), creates draft instead of sending. Set to false to actually send.",
                        "default": True,
                    },
                },
                "required": ["to", "subject", "body_text"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="send_draft",
            description="Send an existing draft email by draft ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "draft_id": {
                        "type": "string",
                        "description": "The ID of the draft to send",
                    }
                },
                "required": ["draft_id"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="delete_email",
            description="Delete a specific email by ID. REQUIRES confirm=True parameter for safety!",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "The ID of the email to delete",
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "MUST be true to actually delete the email. Safety check.",
                        "default": False,
                    },
                },
                "required": ["message_id", "confirm"],
            },
            annotations=_DESTRUCTIVE,
        ),
        types.Tool(
            name="batch_delete_emails",
            description="Delete multiple emails by their IDs. Defaults to dry_run=True for safety!",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of message IDs to delete",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true (default), shows preview without deleting. Set to false to actually delete.",
                        "default": True,
                    },
                },
                "required": ["message_ids"],
            },
            annotations=_DESTRUCTIVE,
        ),
        types.Tool(
            name="gmail_archive",
            description="Archive a Gmail message (remove INBOX). Requires confirm=True.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string"},
                    "confirm": {"type": "boolean", "default": False},
                },
                "required": ["message_id"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="gmail_label_apply",
            description="Apply a label to messages with dry-run preview",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_ids": {"type": "array", "items": {"type": "string"}},
                    "label_name": {"type": "string"},
                    "dry_run": {"type": "boolean", "default": True},
                    "create_if_missing": {"type": "boolean", "default": True},
                },
                "required": ["message_ids", "label_name"],
            },
            annotations=_WRITE,
        ),
        # ── Google Calendar ───────────────────────────────────────────────
        types.Tool(
            name="list_events",
            description="List upcoming calendar events",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string"},
                    "max_results": {"type": "integer"},
                },
                "required": [],
            },
            annotations=_READ_ONLY,
        ),
        types.Tool(
            name="calendar_find_free_slots",
            description="Find free time slots in a calendar",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string", "default": "primary"},
                    "start_time": {
                        "type": "string",
                        "description": "ISO format start time",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "ISO format end time",
                    },
                    "duration_minutes": {"type": "integer", "default": 30},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["start_time", "end_time"],
            },
            annotations=_READ_ONLY,
        ),
        types.Tool(
            name="create_event",
            description="Create a calendar event",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "start_time": {
                        "type": "string",
                        "description": "ISO format start time",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "ISO format end time",
                    },
                    "description": {"type": "string"},
                    "calendar_id": {"type": "string", "default": "primary"},
                },
                "required": ["summary", "start_time", "end_time"],
            },
            annotations=_WRITE,
        ),
        types.Tool(
            name="calendar_create_meeting",
            description="Create a calendar meeting with attendees. Requires confirm=True.",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "start_time": {
                        "type": "string",
                        "description": "ISO format start time",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "ISO format end time",
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "description": {"type": "string"},
                    "location": {"type": "string"},
                    "confirm": {"type": "boolean", "default": False},
                },
                "required": ["summary", "start_time", "end_time"],
            },
            annotations=_WRITE,
        ),
    ]


async def run() -> None:
    config = load_config()
    logger = setup_logging(config.log_file, level=config.log_level)

    server = Server("My Google Tools")

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    @server.list_tools()
    async def handle_list_tools() -> List[types.Tool]:
        return _tools()

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if not arguments:
            arguments = {}

        try:
            require_token_configured(config.mcp_auth_token)

            handlers = {
                "find_files": lambda a: find_files_handler(config, logger, a.get("query")),
                "read_sheet": lambda a: read_sheet_handler(
                    config, logger, a.get("spreadsheet_id"), a.get("range_name")
                ),
                "append_row": lambda a: append_row_handler(
                    config, logger, a.get("spreadsheet_id"), a.get("range_name"), a.get("values")
                ),
                "update_sheet": lambda a: update_sheet_handler(
                    config, logger, a.get("spreadsheet_id"), a.get("range_name"), a.get("values")
                ),
                "create_script_project": lambda a: create_script_project_handler(
                    config, logger, a.get("title"), a.get("parent_id")
                ),
                "get_script_content": lambda a: get_script_content_handler(
                    config, logger, a.get("script_id")
                ),
                "prepare_script_update": lambda a: prepare_script_update_handler(
                    config, logger, a.get("script_id"), a.get("files")
                ),
                "execute_operation": lambda a: execute_operation_handler(
                    config, logger, a.get("operation_id")
                ),
                "cancel_operation": lambda a: cancel_operation_handler(
                    config, logger, a.get("operation_id")
                ),
                "restore_script_backup": lambda a: restore_script_backup_handler(
                    config, logger, a.get("backup_path")
                ),
                "read_doc": lambda a: read_doc_handler(config, logger, a.get("document_id")),
                "create_doc": lambda a: create_doc_handler(config, logger, a.get("title")),
                "append_to_doc": lambda a: append_to_doc_handler(
                    config, logger, a.get("document_id"), a.get("text")
                ),
                "doc_fill_template": lambda a: doc_fill_template_handler(
                    config, logger, a.get("document_id"), a.get("replacements"), a.get("confirm", False)
                ),
                "doc_export_pdf": lambda a: doc_export_pdf_handler(
                    config, logger, a.get("document_id")
                ),
                "create_spreadsheet": lambda a: create_spreadsheet_handler(
                    config, logger, a.get("title")
                ),
                "add_sheet": lambda a: add_sheet_handler(
                    config, logger, a.get("spreadsheet_id"), a.get("title")
                ),
                "clear_range": lambda a: clear_range_handler(
                    config, logger, a.get("spreadsheet_id"), a.get("range_name"), a.get("confirm", False)
                ),
                "sheet_create_filter_view": lambda a: sheet_create_filter_view_handler(
                    config,
                    logger,
                    a.get("spreadsheet_id"),
                    a.get("sheet_id"),
                    a.get("title"),
                    a.get("start_row", 0),
                    a.get("end_row"),
                    a.get("start_col", 0),
                    a.get("end_col"),
                ),
                "sheet_export_csv": lambda a: sheet_export_csv_handler(
                    config, logger, a.get("spreadsheet_id"), a.get("range_name"), a.get("max_rows", 5000)
                ),
                "sheet_find_replace": lambda a: sheet_find_replace_handler(
                    config,
                    logger,
                    a.get("spreadsheet_id"),
                    a.get("range_name"),
                    a.get("find_text"),
                    a.get("replace_text"),
                    a.get("dry_run", True),
                    a.get("match_case", False),
                ),
                "sheet_create_named_range": lambda a: sheet_create_named_range_handler(
                    config,
                    logger,
                    a.get("spreadsheet_id"),
                    a.get("name"),
                    a.get("sheet_id"),
                    a.get("start_row"),
                    a.get("end_row"),
                    a.get("start_col"),
                    a.get("end_col"),
                ),
                "get_spreadsheet_meta": lambda a: get_spreadsheet_meta_handler(
                    config, logger, a.get("spreadsheet_id")
                ),
                "send_email": lambda a: send_email_handler(
                    config, logger, a.get("to"), a.get("subject"), a.get("body_text"), a.get("draft_mode", True)
                ),
                "send_draft": lambda a: send_draft_handler(config, logger, a.get("draft_id")),
                "get_gmail_profile": lambda a: get_gmail_profile_handler(config, logger),
                "create_draft": lambda a: create_draft_handler(
                    config, logger, a.get("to"), a.get("subject"), a.get("body_text")
                ),
                "list_emails": lambda a: list_emails_handler(
                    config, logger, a.get("max_results", 10), a.get("query")
                ),
                "read_email": lambda a: read_email_handler(config, logger, a.get("message_id")),
                "delete_email": lambda a: delete_email_handler(
                    config, logger, a.get("message_id"), a.get("confirm", False)
                ),
                "batch_delete_emails": lambda a: batch_delete_emails_handler(
                    config, logger, a.get("message_ids"), a.get("dry_run", True)
                ),
                "gmail_search_and_summarize": lambda a: gmail_search_and_summarize_handler(
                    config, logger, a.get("query"), a.get("max_results", 50)
                ),
                "gmail_archive": lambda a: gmail_archive_handler(
                    config, logger, a.get("message_id"), a.get("confirm", False)
                ),
                "gmail_label_apply": lambda a: gmail_label_apply_handler(
                    config,
                    logger,
                    a.get("message_ids"),
                    a.get("label_name"),
                    a.get("dry_run", True),
                    a.get("create_if_missing", True),
                ),
                "list_events": lambda a: list_events_handler(
                    config, logger, a.get("calendar_id", "primary"), a.get("max_results", 10)
                ),
                "create_event": lambda a: create_event_handler(
                    config,
                    logger,
                    a.get("summary"),
                    a.get("start_time"),
                    a.get("end_time"),
                    a.get("description", ""),
                    a.get("calendar_id", "primary"),
                ),
                "calendar_find_free_slots": lambda a: calendar_find_free_slots_handler(
                    config,
                    logger,
                    a.get("calendar_id", "primary"),
                    a.get("start_time"),
                    a.get("end_time"),
                    a.get("duration_minutes", 30),
                    a.get("max_results", 5),
                ),
                "calendar_create_meeting": lambda a: calendar_create_meeting_handler(
                    config,
                    logger,
                    a.get("summary"),
                    a.get("start_time"),
                    a.get("end_time"),
                    a.get("attendees"),
                    a.get("description", ""),
                    a.get("location", ""),
                    a.get("confirm", False),
                ),
                "create_folder": lambda a: create_folder_handler(
                    config, logger, a.get("name"), a.get("parent_id")
                ),
                "move_file": lambda a: move_file_handler(
                    config, logger, a.get("file_id"), a.get("folder_id")
                ),
                "share_file": lambda a: share_file_handler(
                    config,
                    logger,
                    a.get("file_id"),
                    a.get("role"),
                    a.get("type", "user"),
                    a.get("email_address"),
                    a.get("allow_public", False),
                ),
                "drive_search_advanced": lambda a: drive_search_advanced_handler(
                    config, logger, a.get("query"), a.get("limit", 50)
                ),
                "drive_list_permissions": lambda a: drive_list_permissions_handler(
                    config, logger, a.get("file_id")
                ),
                "drive_revoke_public": lambda a: drive_revoke_public_handler(
                    config, logger, a.get("file_id"), a.get("confirm", False)
                ),
                "drive_copy_file": lambda a: drive_copy_file_handler(
                    config, logger, a.get("file_id"), a.get("name"), a.get("parent_id")
                ),
            }

            if name not in handlers:
                raise ValueError(f"Unknown tool: {name}")

            result = await asyncio.to_thread(handlers[name], arguments)

            if isinstance(result, BinaryResult):
                return [
                    types.EmbeddedResource(
                        type="resource",
                        resource=types.BlobResourceContents(
                            uri=result.uri,
                            mimeType=result.mime_type,
                            blob=base64.b64encode(result.data).decode(),
                        ),
                    )
                ]

            return [types.TextContent(type="text", text=str(result))]

        except Exception as e:
            logger.exception("Tool call error [%s]: %s", name, e)
            return [types.TextContent(type="text", text=f"Error: {str(e)}", isError=True)]

    # ------------------------------------------------------------------
    # Resources
    # ------------------------------------------------------------------

    @server.list_resources()
    async def handle_list_resources() -> List[types.Resource]:
        return [
            types.Resource(
                uri="gdrive://recent",
                name="Recent Google Drive Files",
                description="Lists the 20 most recently modified files in Google Drive",
                mimeType="text/plain",
            ),
            types.Resource(
                uri="gmail://inbox",
                name="Gmail Inbox",
                description="Recent unread messages in the Gmail inbox",
                mimeType="text/plain",
            ),
            types.Resource(
                uri="gcalendar://upcoming",
                name="Upcoming Calendar Events",
                description="Upcoming events from the primary Google Calendar (next 7 days)",
                mimeType="text/plain",
            ),
        ]

    @server.list_resource_templates()
    async def handle_list_resource_templates() -> List[types.ResourceTemplate]:
        return [
            types.ResourceTemplate(
                uriTemplate="gdrive://file/{file_id}",
                name="Google Drive File",
                description="Metadata for a specific Google Drive file (ID required)",
                mimeType="text/plain",
            ),
            types.ResourceTemplate(
                uriTemplate="gsheets://{spreadsheet_id}/{range}",
                name="Google Sheets Range",
                description=(
                    "Data from a specific spreadsheet range, e.g. "
                    "gsheets://SPREADSHEET_ID/Sheet1!A1:Z100"
                ),
                mimeType="text/plain",
            ),
            types.ResourceTemplate(
                uriTemplate="gdocs://{document_id}",
                name="Google Document",
                description="Full text content of a specific Google Doc (ID required)",
                mimeType="text/plain",
            ),
        ]

    @server.read_resource()
    async def handle_read_resource(uri: AnyUrl) -> Iterable[ReadResourceContents]:
        from .auth import get_creds
        from googleapiclient.discovery import build

        uri_str = str(uri)

        def _fetch() -> str:
            if uri_str == "gdrive://recent":
                creds = get_creds(config)
                svc = build("drive", "v3", credentials=creds)
                results = svc.files().list(
                    orderBy="modifiedTime desc",
                    pageSize=20,
                    fields="files(id,name,mimeType,modifiedTime,owners)",
                ).execute()
                files = results.get("files", [])
                if not files:
                    return "No files found."
                lines = ["Recent Google Drive files (by last modified):\n"]
                for f in files:
                    owners = f.get("owners", [{}])
                    owner = owners[0].get("emailAddress", "?") if owners else "?"
                    lines.append(
                        f"- {f['name']} (ID: {f['id']}) [{f.get('mimeType', '?')}] "
                        f"modified={f.get('modifiedTime', '')} owner={owner}"
                    )
                return "\n".join(lines)

            elif uri_str == "gmail://inbox":
                creds = get_creds(config)
                svc = build("gmail", "v1", credentials=creds)
                results = svc.users().messages().list(
                    userId="me", maxResults=20, q="is:unread in:inbox"
                ).execute()
                messages = results.get("messages", [])
                if not messages:
                    return "No unread messages in inbox."
                lines = [f"Unread inbox messages ({len(messages)}):\n"]
                for msg in messages:
                    full = svc.users().messages().get(
                        userId="me",
                        id=msg["id"],
                        format="metadata",
                        metadataHeaders=["From", "Subject", "Date"],
                    ).execute()
                    hdrs = {
                        h["name"]: h["value"]
                        for h in full.get("payload", {}).get("headers", [])
                    }
                    lines.append(
                        f"- [{msg['id']}] {hdrs.get('Date', '')} | "
                        f"{hdrs.get('From', '')} | {hdrs.get('Subject', '(no subject)')}"
                    )
                return "\n".join(lines)

            elif uri_str == "gcalendar://upcoming":
                creds = get_creds(config)
                svc = build("calendar", "v3", credentials=creds)
                now = datetime.now(timezone.utc)
                time_max = (now + timedelta(days=7)).isoformat()
                results = svc.events().list(
                    calendarId="primary",
                    timeMin=now.isoformat(),
                    timeMax=time_max,
                    maxResults=25,
                    singleEvents=True,
                    orderBy="startTime",
                ).execute()
                events = results.get("items", [])
                if not events:
                    return "No upcoming events in the next 7 days."
                lines = ["Upcoming calendar events (next 7 days):\n"]
                for ev in events:
                    start = ev.get("start", {}).get(
                        "dateTime", ev.get("start", {}).get("date", "?")
                    )
                    lines.append(
                        f"- {start} | {ev.get('summary', '(no title)')} (ID: {ev.get('id')})"
                    )
                return "\n".join(lines)

            elif uri_str.startswith("gdrive://file/"):
                file_id = uri_str.removeprefix("gdrive://file/")
                if not file_id:
                    raise ValueError("file_id is required in gdrive://file/{file_id}")
                creds = get_creds(config)
                svc = build("drive", "v3", credentials=creds)
                f = svc.files().get(
                    fileId=file_id,
                    fields="id,name,mimeType,size,createdTime,modifiedTime,owners,webViewLink,parents",
                ).execute()
                owners = f.get("owners", [{}])
                owner = owners[0].get("emailAddress", "?") if owners else "?"
                size_bytes = int(f.get("size", 0))
                return (
                    f"File: {f.get('name')}\n"
                    f"ID: {f.get('id')}\n"
                    f"Type: {f.get('mimeType')}\n"
                    f"Size: {size_bytes:,} bytes\n"
                    f"Created: {f.get('createdTime')}\n"
                    f"Modified: {f.get('modifiedTime')}\n"
                    f"Owner: {owner}\n"
                    f"Link: {f.get('webViewLink', 'N/A')}"
                )

            elif uri_str.startswith("gsheets://"):
                # URI form: gsheets://{spreadsheet_id}/{range}
                remainder = uri_str.removeprefix("gsheets://")
                parts = remainder.split("/", 1)
                spreadsheet_id = parts[0]
                range_name = parts[1] if len(parts) > 1 else "Sheet1"
                if not spreadsheet_id:
                    raise ValueError("spreadsheet_id is required in gsheets://{spreadsheet_id}/{range}")
                creds = get_creds(config)
                svc = build("sheets", "v4", credentials=creds)
                result = svc.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id, range=range_name
                ).execute()
                values = result.get("values", [])
                if not values:
                    return "No data found."
                rows = [
                    "| " + " | ".join(str(c) for c in row) + " |"
                    for row in values
                ]
                return f"Sheet data ({range_name}):\n" + "\n".join(rows)

            elif uri_str.startswith("gdocs://"):
                document_id = uri_str.removeprefix("gdocs://")
                if not document_id:
                    raise ValueError("document_id is required in gdocs://{document_id}")
                creds = get_creds(config)
                svc = build("docs", "v1", credentials=creds)
                doc = svc.documents().get(documentId=document_id).execute()
                content = doc.get("body", {}).get("content", [])
                text_parts = []
                for value in content:
                    if "paragraph" in value:
                        for elem in value["paragraph"].get("elements", []):
                            text_parts.append(elem.get("textRun", {}).get("content", ""))
                return f"Document: {doc.get('title')}\n\n{''.join(text_parts)}"

            else:
                raise ValueError(f"Unknown resource URI scheme: {uri_str}")

        text = await asyncio.to_thread(_fetch)
        return [ReadResourceContents(content=text, mime_type="text/plain")]

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    @server.list_prompts()
    async def handle_list_prompts() -> List[types.Prompt]:
        return [
            types.Prompt(
                name="summarize_inbox",
                description=(
                    "Fetch recent Gmail messages and prepare them for AI summarization. "
                    "Optionally filter by a Gmail search query."
                ),
                arguments=[
                    types.PromptArgument(
                        name="query",
                        description="Gmail search query (default: 'is:unread in:inbox')",
                        required=False,
                    ),
                    types.PromptArgument(
                        name="max_results",
                        description="Maximum number of emails to include (default: 20)",
                        required=False,
                    ),
                ],
            ),
            types.Prompt(
                name="analyze_spreadsheet",
                description=(
                    "Read a Google Sheet range and prepare the data for AI analysis "
                    "or visualization."
                ),
                arguments=[
                    types.PromptArgument(
                        name="spreadsheet_id",
                        description="The Google Spreadsheet ID",
                        required=True,
                    ),
                    types.PromptArgument(
                        name="range",
                        description="Sheet range to read (default: Sheet1)",
                        required=False,
                    ),
                ],
            ),
            types.Prompt(
                name="plan_week",
                description=(
                    "Fetch upcoming calendar events and prepare a weekly planning summary "
                    "for AI-assisted scheduling."
                ),
                arguments=[
                    types.PromptArgument(
                        name="days_ahead",
                        description="Number of days to look ahead (default: 7)",
                        required=False,
                    ),
                ],
            ),
            types.Prompt(
                name="search_drive",
                description=(
                    "Search Google Drive for files and prepare a structured list "
                    "for AI review or organisation suggestions."
                ),
                arguments=[
                    types.PromptArgument(
                        name="query",
                        description="Drive search query (e.g. 'name contains \"budget\"')",
                        required=True,
                    ),
                    types.PromptArgument(
                        name="limit",
                        description="Maximum number of results (default: 20)",
                        required=False,
                    ),
                ],
            ),
        ]

    @server.get_prompt()
    async def handle_get_prompt(
        name: str, arguments: dict[str, str] | None
    ) -> types.GetPromptResult:
        from .auth import get_creds
        from googleapiclient.discovery import build

        args = arguments or {}

        if name == "summarize_inbox":
            query = args.get("query", "is:unread in:inbox")
            max_results = int(args.get("max_results", "20"))

            def _fetch_emails() -> str:
                creds = get_creds(config)
                svc = build("gmail", "v1", credentials=creds)
                results = svc.users().messages().list(
                    userId="me", maxResults=min(max_results, 50), q=query
                ).execute()
                messages = results.get("messages", [])
                if not messages:
                    return f"No messages found for query: {query}"
                lines = [f"Found {len(messages)} message(s) for '{query}':\n"]
                for msg in messages:
                    full = svc.users().messages().get(
                        userId="me",
                        id=msg["id"],
                        format="metadata",
                        metadataHeaders=["From", "Subject", "Date"],
                    ).execute()
                    hdrs = {
                        h["name"]: h["value"]
                        for h in full.get("payload", {}).get("headers", [])
                    }
                    snippet = full.get("snippet", "")[:120]
                    lines.append(
                        f"\n---\nID: {msg['id']}\n"
                        f"Date: {hdrs.get('Date', '')}\n"
                        f"From: {hdrs.get('From', '')}\n"
                        f"Subject: {hdrs.get('Subject', '(no subject)')}\n"
                        f"Preview: {snippet}"
                    )
                return "\n".join(lines)

            email_data = await asyncio.to_thread(_fetch_emails)
            return types.GetPromptResult(
                description=f"Gmail inbox summary — query: {query}",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=(
                                f"Here are the recent emails from Gmail (query: '{query}'):\n\n"
                                f"{email_data}\n\n"
                                "Please summarize these emails, grouping by sender or topic where "
                                "relevant. Highlight any urgent or action-required items."
                            ),
                        ),
                    )
                ],
            )

        elif name == "analyze_spreadsheet":
            spreadsheet_id = args.get("spreadsheet_id", "")
            if not spreadsheet_id:
                raise ValueError("spreadsheet_id is required for the analyze_spreadsheet prompt")
            range_name = args.get("range", "Sheet1")

            def _fetch_sheet() -> tuple[str, str]:
                creds = get_creds(config)
                svc = build("sheets", "v4", credentials=creds)
                meta = svc.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
                title = meta.get("properties", {}).get("title", spreadsheet_id)
                result = svc.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id, range=range_name
                ).execute()
                values = result.get("values", [])
                if not values:
                    return title, "No data found in the specified range."
                rows = [
                    "| " + " | ".join(str(c) for c in row) + " |"
                    for row in values[:200]
                ]
                return title, "\n".join(rows)

            title, sheet_data = await asyncio.to_thread(_fetch_sheet)
            return types.GetPromptResult(
                description=f"Analysis prompt for spreadsheet: {title}",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=(
                                f"Here is data from Google Spreadsheet '{title}' "
                                f"(range: {range_name}):\n\n"
                                f"{sheet_data}\n\n"
                                "Please analyse this data. Identify patterns, trends, and notable "
                                "insights. If there are headers in the first row, use them to "
                                "understand the data structure."
                            ),
                        ),
                    )
                ],
            )

        elif name == "plan_week":
            days_ahead = int(args.get("days_ahead", "7"))

            def _fetch_events() -> str:
                creds = get_creds(config)
                svc = build("calendar", "v3", credentials=creds)
                now = datetime.now(timezone.utc)
                time_max = (now + timedelta(days=days_ahead)).isoformat()
                results = svc.events().list(
                    calendarId="primary",
                    timeMin=now.isoformat(),
                    timeMax=time_max,
                    maxResults=50,
                    singleEvents=True,
                    orderBy="startTime",
                ).execute()
                events = results.get("items", [])
                if not events:
                    return f"No events in the next {days_ahead} days."
                lines = [f"Calendar events for the next {days_ahead} days:\n"]
                for ev in events:
                    start = ev.get("start", {}).get(
                        "dateTime", ev.get("start", {}).get("date", "?")
                    )
                    end = ev.get("end", {}).get(
                        "dateTime", ev.get("end", {}).get("date", "?")
                    )
                    attendees = ev.get("attendees", [])
                    att_list = (
                        ", ".join(a.get("email", "") for a in attendees[:5])
                        if attendees
                        else "none"
                    )
                    lines.append(
                        f"- {start} → {end}\n"
                        f"  Title: {ev.get('summary', '(no title)')}\n"
                        f"  Attendees: {att_list}\n"
                        f"  ID: {ev.get('id')}"
                    )
                return "\n".join(lines)

            events_data = await asyncio.to_thread(_fetch_events)
            return types.GetPromptResult(
                description=f"Weekly planning — next {days_ahead} days",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=(
                                f"{events_data}\n\n"
                                "Based on these calendar events, please help me plan my week. "
                                "Identify busy periods, suggest preparation for important meetings, "
                                "and highlight any scheduling conflicts or time blocks that need "
                                "attention."
                            ),
                        ),
                    )
                ],
            )

        elif name == "search_drive":
            query = args.get("query", "")
            if not query:
                raise ValueError("query is required for the search_drive prompt")
            limit = int(args.get("limit", "20"))

            def _fetch_drive() -> str:
                creds = get_creds(config)
                svc = build("drive", "v3", credentials=creds)
                results = svc.files().list(
                    q=query,
                    pageSize=min(limit, 50),
                    fields="files(id,name,mimeType,modifiedTime,owners,webViewLink)",
                ).execute()
                files = results.get("files", [])
                if not files:
                    return f"No files found for: {query}"
                lines = [f"Found {len(files)} file(s) for query '{query}':\n"]
                for f in files:
                    owners = f.get("owners", [{}])
                    owner = owners[0].get("emailAddress", "?") if owners else "?"
                    lines.append(
                        f"- {f.get('name')}\n"
                        f"  ID: {f.get('id')} | Type: {f.get('mimeType', '?')}\n"
                        f"  Modified: {f.get('modifiedTime', '')} | Owner: {owner}\n"
                        f"  Link: {f.get('webViewLink', 'N/A')}"
                    )
                return "\n".join(lines)

            drive_data = await asyncio.to_thread(_fetch_drive)
            return types.GetPromptResult(
                description=f"Drive search results — query: {query}",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=(
                                f"{drive_data}\n\n"
                                "Please review these Google Drive files and provide a summary "
                                "report. Group related files, identify the most recently modified "
                                "ones, and suggest any organisation improvements if relevant."
                            ),
                        ),
                    )
                ],
            )

        else:
            raise ValueError(f"Unknown prompt: {name}")

    # ------------------------------------------------------------------
    # Start server
    # ------------------------------------------------------------------

    async with stdio_server() as (read, write):
        await server.run(
            read_stream=read,
            write_stream=write,
            initialization_options=server.create_initialization_options(),
        )
