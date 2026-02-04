# MCP Tools Reference

Below is a list of tools available in this MCP server.

## Drive
- `find_files(query)`
  - Search by name or full Drive query.
- `create_folder(name, parent_id?)`
  - Create a folder; `parent_id` is optional.
- `move_file(file_id, folder_id)`
  - Move a file to a folder.
- `share_file(file_id, role, type?, email_address?, allow_public?)`
  - `type`: `user|group|domain|anyone`, public access only with `allow_public=true`.
- `drive_search_advanced(query, limit?)`
  - Full Drive query syntax.
- `drive_list_permissions(file_id)`
  - List permissions.
- `drive_revoke_public(file_id, confirm?)`
  - Revoke public access, requires `confirm=true`.
- `drive_copy_file(file_id, name?, parent_id?)`
  - Copy a file.

## Sheets
- `read_sheet(spreadsheet_id, range_name)`
  - Read a range.
- `append_row(spreadsheet_id, range_name, values[])`
  - Append a row.
- `update_sheet(spreadsheet_id, range_name, values[][])`
  - Update a range with rows.
- `create_spreadsheet(title)`
  - Create a spreadsheet.
- `add_sheet(spreadsheet_id, title)`
  - Add a sheet (tab).
- `clear_range(spreadsheet_id, range_name, confirm?)`
  - Large ranges require `confirm=true`.
- `sheet_create_filter_view(spreadsheet_id, sheet_id, title, start_row?, end_row?, start_col?, end_col?)`
  - Create a filter view.
- `sheet_export_csv(spreadsheet_id, range_name, max_rows?)`
  - Export a range to CSV.
- `sheet_find_replace(spreadsheet_id, range_name, find_text, replace_text, dry_run?, match_case?)`
  - Defaults to `dry_run=true`.
- `sheet_create_named_range(spreadsheet_id, name, sheet_id, start_row, end_row, start_col, end_col)`
  - Named range by grid indexes.
- `get_spreadsheet_meta(spreadsheet_id)`
  - Spreadsheet metadata.

## Docs
- `read_doc(document_id)`
  - Read document text.
- `create_doc(title)`
  - Create a document.
- `append_to_doc(document_id, text)`
  - Append text.
- `doc_fill_template(document_id, replacements, confirm?)`
  - Fill a template, requires `confirm=true`.
- `doc_export_pdf(document_id)`
  - Export PDF (base64).

## Gmail
- `send_email(to, subject, body_text, draft_mode?)`
  - Defaults to draft mode.
- `send_draft(draft_id)`
  - Send a draft.
- `get_gmail_profile()`
  - Get authenticated address.
- `create_draft(to, subject, body_text)`
  - Create a draft.
- `list_emails(max_results?, query?)`
  - List emails.
- `read_email(message_id)`
  - Read an email (snippet).
- `delete_email(message_id, confirm?)`
  - Requires `confirm=true`.
- `batch_delete_emails(message_ids[], dry_run?)`
  - Defaults to `dry_run=true`.
- `gmail_search_and_summarize(query, max_results?)`
  - Search with a short summary.
- `gmail_archive(message_id, confirm?)`
  - Requires `confirm=true`.
- `gmail_label_apply(message_ids[], label_name, dry_run?, create_if_missing?)`
  - Defaults to `dry_run=true`.

## Calendar
- `list_events(calendar_id?, max_results?)`
  - List upcoming events.
- `create_event(summary, start_time, end_time, description?)`
  - Create an event.
- `calendar_find_free_slots(calendar_id?, start_time, end_time, duration_minutes?, max_results?)`
  - Find free slots.
- `calendar_create_meeting(summary, start_time, end_time, attendees?, description?, location?, confirm?)`
  - Requires `confirm=true`.

## Apps Script
- `create_script_project(title, parent_id?)`
  - Create an Apps Script project.
- `get_script_content(script_id)`
  - Get project content.
- `prepare_script_update(script_id, files[])`
  - Prepare update, returns `operation_id`.
- `execute_operation(operation_id)`
  - Execute prepared operation.
- `cancel_operation(operation_id)`
  - Cancel prepared operation.
- `restore_script_backup(backup_path)`
  - Restore from backup.
