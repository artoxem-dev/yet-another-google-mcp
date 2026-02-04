from typing import List

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from .config import load_config
from .logging import setup_logging
from .security import require_auth
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

config = load_config()
logger = setup_logging(config.log_file)

server = Server("My Google Tools")


@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="find_files",
            description="Search for files on Google Drive. Query example: 'name contains \"System\"'",
            inputSchema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
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
        types.Tool(
            name="append_row",
            description="Append a row to a Google Sheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "range_name": {"type": "string"},
                    "values": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["spreadsheet_id", "range_name", "values"],
            },
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
        ),
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
        ),
        types.Tool(
            name="get_script_content",
            description="Get the content of a Google Apps Script project",
            inputSchema={
                "type": "object",
                "properties": {"script_id": {"type": "string"}},
                "required": ["script_id"],
            },
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
        ),
        types.Tool(
            name="read_doc",
            description="Read the content of a Google Doc",
            inputSchema={
                "type": "object",
                "properties": {"document_id": {"type": "string"}},
                "required": ["document_id"],
            },
        ),
        types.Tool(
            name="create_doc",
            description="Create a new Google Doc",
            inputSchema={
                "type": "object",
                "properties": {"title": {"type": "string"}},
                "required": ["title"],
            },
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
        ),
        types.Tool(
            name="doc_export_pdf",
            description="Export a Google Doc to PDF (base64)",
            inputSchema={
                "type": "object",
                "properties": {"document_id": {"type": "string"}},
                "required": ["document_id"],
            },
        ),
        types.Tool(
            name="create_spreadsheet",
            description="Create a new Google Spreadsheet",
            inputSchema={
                "type": "object",
                "properties": {"title": {"type": "string"}},
                "required": ["title"],
            },
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
                "required": [
                    "spreadsheet_id",
                    "range_name",
                    "find_text",
                    "replace_text",
                ],
            },
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
        ),
        types.Tool(
            name="get_spreadsheet_meta",
            description="Get metadata (sheets, titles) of a spreadsheet",
            inputSchema={
                "type": "object",
                "properties": {"spreadsheet_id": {"type": "string"}},
                "required": ["spreadsheet_id"],
            },
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
        ),
        types.Tool(
            name="get_gmail_profile",
            description="Get the authenticated Gmail address for the current OAuth token",
            inputSchema={"type": "object", "properties": {}},
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
            },
        ),
        types.Tool(
            name="read_email",
            description="Read a specific email by ID",
            inputSchema={
                "type": "object",
                "properties": {"message_id": {"type": "string"}},
                "required": ["message_id"],
            },
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
        ),
        types.Tool(
            name="list_events",
            description="List upcoming calendar events",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string"},
                    "max_results": {"type": "integer"},
                },
            },
        ),
        types.Tool(
            name="create_event",
            description="Create a calendar event",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "start_time": {"type": "string", "description": "ISO format start time"},
                    "end_time": {"type": "string", "description": "ISO format end time"},
                    "description": {"type": "string"},
                },
                "required": ["summary", "start_time", "end_time"],
            },
        ),
        types.Tool(
            name="calendar_find_free_slots",
            description="Find free time slots in a calendar",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string", "default": "primary"},
                    "start_time": {"type": "string", "description": "ISO format start time"},
                    "end_time": {"type": "string", "description": "ISO format end time"},
                    "duration_minutes": {"type": "integer", "default": 30},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["start_time", "end_time"],
            },
        ),
        types.Tool(
            name="calendar_create_meeting",
            description="Create a calendar meeting with attendees. Requires confirm=True.",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "start_time": {"type": "string", "description": "ISO format start time"},
                    "end_time": {"type": "string", "description": "ISO format end time"},
                    "attendees": {"type": "array", "items": {"type": "string"}},
                    "description": {"type": "string"},
                    "location": {"type": "string"},
                    "confirm": {"type": "boolean", "default": False},
                },
                "required": ["summary", "start_time", "end_time"],
            },
        ),
        types.Tool(
            name="create_folder",
            description="Create a folder in Google Drive",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string"}, "parent_id": {"type": "string"}},
                "required": ["name"],
            },
        ),
        types.Tool(
            name="move_file",
            description="Move a file to a different folder",
            inputSchema={
                "type": "object",
                "properties": {"file_id": {"type": "string"}, "folder_id": {"type": "string"}},
                "required": ["file_id", "folder_id"],
            },
        ),
        types.Tool(
            name="share_file",
            description="Share a file with a user or make it public. REQUIRES allow_public=True to share publicly!",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {"type": "string"},
                    "role": {"type": "string", "enum": ["reader", "commenter", "writer"]},
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
        ),
        types.Tool(
            name="drive_list_permissions",
            description="List permissions for a Drive file",
            inputSchema={
                "type": "object",
                "properties": {"file_id": {"type": "string"}},
                "required": ["file_id"],
            },
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
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if not arguments:
        arguments = {}

    try:
        require_auth(arguments, config.mcp_auth_token)

        handlers = {
            "find_files": lambda a: find_files_handler(
                config, logger, a.get("query")
            ),
            "read_sheet": lambda a: read_sheet_handler(
                config, logger, a.get("spreadsheet_id"), a.get("range_name")
            ),
            "append_row": lambda a: append_row_handler(
                config,
                logger,
                a.get("spreadsheet_id"),
                a.get("range_name"),
                a.get("values"),
            ),
            "update_sheet": lambda a: update_sheet_handler(
                config,
                logger,
                a.get("spreadsheet_id"),
                a.get("range_name"),
                a.get("values"),
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
            "read_doc": lambda a: read_doc_handler(
                config, logger, a.get("document_id")
            ),
            "create_doc": lambda a: create_doc_handler(
                config, logger, a.get("title")
            ),
            "append_to_doc": lambda a: append_to_doc_handler(
                config, logger, a.get("document_id"), a.get("text")
            ),
            "doc_fill_template": lambda a: doc_fill_template_handler(
                config,
                logger,
                a.get("document_id"),
                a.get("replacements"),
                a.get("confirm", False),
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
                config,
                logger,
                a.get("spreadsheet_id"),
                a.get("range_name"),
                a.get("confirm", False),
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
                config,
                logger,
                a.get("spreadsheet_id"),
                a.get("range_name"),
                a.get("max_rows", 5000),
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
                config,
                logger,
                a.get("to"),
                a.get("subject"),
                a.get("body_text"),
                a.get("draft_mode", True),
            ),
            "send_draft": lambda a: send_draft_handler(
                config, logger, a.get("draft_id")
            ),
            "get_gmail_profile": lambda a: get_gmail_profile_handler(config, logger),
            "create_draft": lambda a: create_draft_handler(
                config, logger, a.get("to"), a.get("subject"), a.get("body_text")
            ),
            "list_emails": lambda a: list_emails_handler(
                config, logger, a.get("max_results", 10), a.get("query")
            ),
            "read_email": lambda a: read_email_handler(
                config, logger, a.get("message_id")
            ),
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
                config,
                logger,
                a.get("file_id"),
                a.get("name"),
                a.get("parent_id"),
            ),
        }

        if name not in handlers:
            raise ValueError(f"Unknown tool: {name}")

        result = handlers[name](arguments)
        return [types.TextContent(type="text", text=str(result))]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def run() -> None:
    async with stdio_server() as (read, write):
        await server.run(
            read_stream=read,
            write_stream=write,
            initialization_options=server.create_initialization_options(),
        )
