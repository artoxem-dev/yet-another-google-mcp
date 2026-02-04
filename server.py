import asyncio

from mcp_google.server import run


if __name__ == "__main__":
    asyncio.run(run())
import base64
from email.mime.text import MIMEText
import asyncio
import json
import os.path
import re
import uuid
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from mcp_google.config import load_config

# Configuration
config = load_config()
CLIENT_SECRETS_FILE = config.client_secrets_file
TOKEN_FILE = config.token_file
BACKUP_DIR = config.backup_dir
LOG_FILE = config.log_file
MCP_AUTH_TOKEN = config.mcp_auth_token

# Setup logging
log_handlers = [logging.StreamHandler()]
if LOG_FILE:
    log_handlers.insert(0, logging.FileHandler(LOG_FILE))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger("GoogleToolsMCP")

# Global storage for pending operations
pending_operations = {}

# Email validation regex
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

SCOPES = config.scopes

def get_creds():
    """Gets credentials using OAuth 2.0 User Flow."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            creds = None
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                 raise FileNotFoundError(
                     "Client secrets file not found at "
                     f"{CLIENT_SECRETS_FILE}. Set GOOGLE_CLIENT_SECRETS_FILE "
                     "or config.yaml client_secrets_file."
                 )
                 
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return creds

# ============================================================================
# SECURITY HELPERS
# ============================================================================

def validate_email(email: str) -> bool:
    """Validate email format"""
    return re.match(EMAIL_REGEX, email) is not None

def create_backup(data: Any, backup_type: str, identifier: str) -> str:
    """Create a backup file and return its path"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{backup_type}_{identifier}_{timestamp}.json"
    filepath = os.path.join(BACKUP_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Backup created: {filepath}")
    return filepath

def cleanup_expired_operations():
    """Remove operations older than 10 minutes"""
    now = datetime.now()
    expired = []
    for op_id, op in pending_operations.items():
        created = datetime.fromisoformat(op['created_at'])
        if now - created > timedelta(minutes=10):
            expired.append(op_id)
    
    for op_id in expired:
        del pending_operations[op_id]
        logger.info(f"Expired operation removed: {op_id}")

def require_auth(arguments: Dict[str, Any]) -> None:
    """Require auth token for all tool calls"""
    if not MCP_AUTH_TOKEN:
        raise ValueError(
            "MCP_AUTH_TOKEN is not set. Set environment variable MCP_AUTH_TOKEN "
            "to enable MCP access."
        )
    provided = arguments.get("auth_token")
    if not provided or provided != MCP_AUTH_TOKEN:
        raise ValueError("Unauthorized: invalid or missing auth_token.")

# Define tool handlers
def find_files_handler(query: str) -> str:
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        
        if "contains" not in query and "=" not in query:
            q = f"name contains '{query}' and trashed = false"
        else:
            q = query

        results = service.files().list(
            q=q, pageSize=10, fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            return "No files found."
            
        output = "Found files:\n"
        for item in items:
            output += f"- {item['name']} (ID: {item['id']}) [{item['mimeType']}]\n"
            
        return output
    except Exception as e:
        return f"Error searching files: {str(e)}"

def read_sheet_handler(spreadsheet_id: str, range_name: str) -> str:
    try:
        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)
        
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                    range=range_name).execute()
        values = result.get('values', [])
        
        if not values:
            return "No data found."
            
        output = f"Data from sheet (range {range_name}):\n"
        for row in values:
            output += f"| {' | '.join(row)} |\n"
            
        return output
    except Exception as e:
        return f"Error reading sheet: {str(e)}"

def append_row_handler(spreadsheet_id: str, range_name: str, values: List[str]) -> str:
    try:
        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)
        
        body = {'values': [values]}
        
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption="USER_ENTERED", body=body).execute()
            
        return f"Successfully appended {result.get('updates').get('updatedCells')} cells."
    except Exception as e:
        return f"Error appending row: {str(e)}"

def update_sheet_handler(spreadsheet_id: str, range_name: str, values: List[List[str]]) -> str:
    try:
        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)
        
        body = {'values': values}
        
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption="USER_ENTERED", body=body).execute()
            
        return f"Successfully updated {result.get('updatedCells')} cells."
    except Exception as e:
        return f"Error updating sheet: {str(e)}"

def create_script_project_handler(title: str, parent_id: str = None) -> str:
    try:
        creds = get_creds()
        service = build('script', 'v1', credentials=creds)
        
        request = {'title': title}
        if parent_id:
            request['parentId'] = parent_id
            
        response = service.projects().create(body=request).execute()
        return f"Script created: {response.get('title')} (ID: {response.get('scriptId')})\nURL: {response.get('scriptId')}"
    except Exception as e:
        return f"Error creating script: {str(e)}"

def get_script_content_handler(script_id: str) -> str:
    try:
        creds = get_creds()
        service = build('script', 'v1', credentials=creds)
        
        content = service.projects().getContent(scriptId=script_id).execute()
        files = content.get('files', [])
        
        output = f"Script Content ({script_id}):\n"
        for file in files:
            output += f"\n--- File: {file.get('name')} ({file.get('type')}) ---\n"
            output += file.get('source', '')
            
        return output
    except Exception as e:
        return f"Error reading script content: {str(e)}"

def prepare_script_update_handler(script_id: str, files: List[Dict[str, str]]) -> str:
    """STEP 1: Prepare script update with backup"""
    try:
        cleanup_expired_operations()
        
        creds = get_creds()
        service = build('script', 'v1', credentials=creds)
        
        # Get current content for backup
        current_content = service.projects().getContent(scriptId=script_id).execute()
        current_files = current_content.get('files', [])
        
        # Create operation ID
        op_id = str(uuid.uuid4())[:8]
        
        # Store pending operation
        pending_operations[op_id] = {
            'type': 'script_update',
            'script_id': script_id,
            'backup': current_files,
            'new_files': files,
            'created_at': datetime.now().isoformat()
        }
        
        # Analyze changes
        old_files = {f['name']: f for f in current_files}
        new_files = {f['name']: f for f in files}
        
        changes = []
        for name in new_files:
            if name not in old_files:
                changes.append(f"  + NEW: {name}")
            else:
                old_lines = old_files[name].get('source', '').count('\n')
                new_lines = new_files[name].get('source', '').count('\n')
                diff = new_lines - old_lines
                changes.append(f"  ~ MODIFIED: {name} ({diff:+d} lines)")
        
        for name in old_files:
            if name not in new_files:
                changes.append(f"  - DELETED: {name}")
        
        result = f"📋 Script Update Prepared (Operation ID: {op_id})\n\n"
        result += f"Script ID: {script_id}\n"
        result += f"Backup created: {len(current_files)} file(s)\n\n"
        result += "📊 Changes:\n" + "\n".join(changes) + "\n\n"
        result += f"⏰ Operation expires in: 10 minutes\n\n"
        result += f"✅ To execute: execute_operation(operation_id='{op_id}')\n"
        result += f"❌ To cancel: cancel_operation(operation_id='{op_id}')"
        
        logger.info(f"Script update prepared: {op_id} for {script_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error preparing script update: {str(e)}")
        return f"❌ Error preparing update: {str(e)}"

def execute_operation_handler(operation_id: str) -> str:
    """STEP 2: Execute a prepared operation"""
    try:
        cleanup_expired_operations()
        
        if operation_id not in pending_operations:
            return f"❌ Operation {operation_id} not found or expired"
        
        op = pending_operations[operation_id]
        
        if op['type'] == 'script_update':
            creds = get_creds()
            service = build('script', 'v1', credentials=creds)
            
            # Create backup file
            backup_path = create_backup(
                op['backup'], 
                'script', 
                op['script_id']
            )
            
            # Execute update
            request = {'files': op['new_files']}
            service.projects().updateContent(
                scriptId=op['script_id'], 
                body=request
            ).execute()
            
            # Remove from pending
            del pending_operations[operation_id]
            
            logger.info(f"Script updated: {op['script_id']} (backup: {backup_path})")
            
            return (
                f"✅ Script updated successfully!\n\n"
                f"📊 Results:\n"
                f"  • Files updated: {len(op['new_files'])}\n"
                f"  • Script ID: {op['script_id']}\n\n"
                f"💾 Backup saved to:\n   {backup_path}\n\n"
                f"🔄 To rollback: restore_script_backup(backup_path='{backup_path}')"
            )
        else:
            return f"❌ Unknown operation type: {op['type']}"
            
    except Exception as e:
        logger.error(f"Error executing operation {operation_id}: {str(e)}")
        return f"❌ Error executing operation: {str(e)}"

def cancel_operation_handler(operation_id: str) -> str:
    """Cancel a prepared operation"""
    cleanup_expired_operations()
    
    if operation_id in pending_operations:
        del pending_operations[operation_id]
        logger.info(f"Operation cancelled: {operation_id}")
        return f"✅ Operation {operation_id} cancelled"
    
    return f"❌ Operation {operation_id} not found"

def restore_script_backup_handler(backup_path: str) -> str:
    """Restore script from backup file"""
    try:
        if not os.path.exists(backup_path):
            return f"❌ Backup file not found: {backup_path}"
        
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # Extract script_id from filename
        filename = os.path.basename(backup_path)
        # Format: backup_script_SCRIPTID_OPID_TIMESTAMP.json
        parts = filename.split('_')
        if len(parts) < 3:
            return f"❌ Invalid backup filename format"
        
        script_id = parts[2]
        
        creds = get_creds()
        service = build('script', 'v1', credentials=creds)
        
        request = {'files': backup_data}
        service.projects().updateContent(scriptId=script_id, body=request).execute()
        
        logger.info(f"Script restored from backup: {script_id} <- {backup_path}")
        return f"✅ Script {script_id} restored from backup successfully!"
        
    except Exception as e:
        logger.error(f"Error restoring backup: {str(e)}")
        return f"❌ Error restoring backup: {str(e)}"

# --- Google Docs Handlers ---
def read_doc_handler(document_id: str) -> str:
    try:
        creds = get_creds()
        service = build('docs', 'v1', credentials=creds)
        
        document = service.documents().get(documentId=document_id).execute()
        content = document.get('body').get('content')
        
        text_content = ""
        for value in content:
            if 'paragraph' in value:
                elements = value.get('paragraph').get('elements')
                for elem in elements:
                    text_content += elem.get('textRun', {}).get('content', '')
        
        return f"Document Content ({document.get('title')}):\n{text_content}"
    except Exception as e:
        return f"Error reading document: {str(e)}"

def create_doc_handler(title: str) -> str:
    try:
        creds = get_creds()
        service = build('docs', 'v1', credentials=creds)
        
        body = {'title': title}
        doc = service.documents().create(body=body).execute()
        
        return f"Created document: {doc.get('title')} (ID: {doc.get('documentId')})"
    except Exception as e:
        return f"Error creating document: {str(e)}"

def append_to_doc_handler(document_id: str, text: str) -> str:
    try:
        creds = get_creds()
        service = build('docs', 'v1', credentials=creds)
        
        requests = [
            {
                'insertText': {
                    'endOfSegmentLocation': {
                        'segmentId': ''
                    },
                    'text': text
                }
            }
        ]
        
        result = service.documents().batchUpdate(
            documentId=document_id, body={'requests': requests}).execute()
            
        return "Successfully appended text to document."
    except Exception as e:
        return f"Error appending to document: {str(e)}"

def doc_fill_template_handler(document_id: str, replacements: Dict[str, str], confirm: bool = False) -> str:
    """Fill a Google Doc template by replacing placeholders"""
    try:
        if not replacements:
            return "❌ replacements map is required."

        if not confirm:
            keys = ", ".join(list(replacements.keys())[:20])
            return (
                "⚠️ CONFIRMATION REQUIRED\n\n"
                f"This will replace placeholders in document {document_id}.\n"
                f"Keys: {keys}\n"
                "To proceed, call again with confirm=True."
            )

        creds = get_creds()
        service = build('docs', 'v1', credentials=creds)

        requests = []
        for key, value in replacements.items():
            requests.append({
                'replaceAllText': {
                    'containsText': {'text': key, 'matchCase': True},
                    'replaceText': str(value)
                }
            })

        service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()

        logger.info(f"Doc template filled: {document_id} keys={len(replacements)}")
        return f"✅ Document updated: {len(replacements)} placeholders replaced."
    except Exception as e:
        logger.error(f"Error filling template {document_id}: {str(e)}")
        return f"❌ Error filling template: {str(e)}"

def doc_export_pdf_handler(document_id: str) -> str:
    """Export a Google Doc to PDF (base64)"""
    try:
        creds = get_creds()
        drive = build('drive', 'v3', credentials=creds)

        data = drive.files().export(
            fileId=document_id, mimeType='application/pdf'
        ).execute()

        pdf_b64 = base64.b64encode(data).decode('utf-8')
        logger.info(f"Doc exported to PDF: {document_id} bytes={len(data)}")
        return f"✅ PDF (base64): {pdf_b64}"
    except Exception as e:
        logger.error(f"Error exporting PDF {document_id}: {str(e)}")
        return f"❌ Error exporting PDF: {str(e)}"

# --- Advanced Google Sheets Handlers ---
def create_spreadsheet_handler(title: str) -> str:
    try:
        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)
        
        spreadsheet = {'properties': {'title': title}}
        spreadsheet = service.spreadsheets().create(body=spreadsheet,
                                                    fields='spreadsheetId').execute()
        return f"Created spreadsheet with ID: {spreadsheet.get('spreadsheetId')}"
    except Exception as e:
        return f"Error creating spreadsheet: {str(e)}"

def add_sheet_handler(spreadsheet_id: str, title: str) -> str:
    try:
        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)
        
        requests = [{
            'addSheet': {
                'properties': {
                    'title': title
                }
            }
        }]
        
        body = {'requests': requests}
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body).execute()
            
        return f"Added sheet '{title}' to spreadsheet."
    except Exception as e:
        return f"Error adding sheet: {str(e)}"

def clear_range_handler(spreadsheet_id: str, range_name: str, confirm: bool = False) -> str:
    """Clear range with auto dry-run for large ranges"""
    try:
        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)
        
        # Get current data to analyze
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_name
            ).execute()
            values = result.get('values', [])
            
            rows = len(values)
            cols = max(len(row) for row in values) if values else 0
            total_cells = rows * cols
            filled_cells = sum(len(row) for row in values)
            
        except:
            total_cells = 0
            filled_cells = 0
        
        # Auto dry-run for large ranges (>100 cells)
        if total_cells > 100 and not confirm:
            logger.warning(f"Large range clear blocked: {range_name} ({total_cells} cells)")
            
            result = f"🔍 DRY RUN: Large range detected ({total_cells:,} cells)\n\n"
            result += f"Would clear range: {range_name}\n\n"
            result += f"📊 Current data analysis:\n"
            result += f"  • Total cells: {total_cells:,}\n"
            result += f"  • Filled cells: {filled_cells:,} ({filled_cells/total_cells*100:.1f}%)\n"
            result += f"  • Empty cells: {total_cells-filled_cells:,}\n\n"
            result += f"⚠️ WARNING: This will delete all data in {filled_cells:,} cells\n\n"
            result += f"✅ To proceed: clear_range(..., confirm=True)\n"
            result += f"💡 Safer option: Clear specific columns instead of entire sheet"
            
            return result
        
        # Clear range
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()
        
        logger.info(f"Range cleared: {spreadsheet_id} / {range_name} ({filled_cells} cells)")
        return f"✅ Cleared range {range_name} ({filled_cells:,} cells removed)."
        
    except Exception as e:
        logger.error(f"Error clearing range {range_name}: {str(e)}")
        return f"❌ Error clearing range: {str(e)}"

def sheet_create_filter_view_handler(
    spreadsheet_id: str,
    sheet_id: int,
    title: str,
    start_row: int = 0,
    end_row: int = None,
    start_col: int = 0,
    end_col: int = None
) -> str:
    """Create a filter view for a sheet with a specified grid range"""
    try:
        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)

        # If end_row/end_col not provided, use sheet properties
        if end_row is None or end_col is None:
            meta = service.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                fields="sheets.properties"
            ).execute()
            for s in meta.get('sheets', []):
                props = s.get('properties', {})
                if props.get('sheetId') == sheet_id:
                    grid = props.get('gridProperties', {})
                    if end_row is None:
                        end_row = grid.get('rowCount', 1000)
                    if end_col is None:
                        end_col = grid.get('columnCount', 26)
                    break

        range_obj = {
            "sheetId": sheet_id,
            "startRowIndex": start_row,
            "endRowIndex": end_row,
            "startColumnIndex": start_col,
            "endColumnIndex": end_col
        }

        requests = [{
            "addFilterView": {
                "filter": {
                    "title": title,
                    "range": range_obj
                }
            }
        }]

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests}
        ).execute()

        logger.info(f"Filter view created: {spreadsheet_id} sheet={sheet_id} title={title}")
        return f"✅ Filter view created: {title}"
    except Exception as e:
        logger.error(f"Error creating filter view: {str(e)}")
        return f"❌ Error creating filter view: {str(e)}"

def sheet_export_csv_handler(spreadsheet_id: str, range_name: str, max_rows: int = 5000) -> str:
    """Export range to CSV (values only)"""
    try:
        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)

        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()
        values = result.get('values', [])

        if not values:
            return "No data found."

        # Apply row limit
        values = values[:max_rows]

        def escape_csv(value: str) -> str:
            value = "" if value is None else str(value)
            if any(c in value for c in [',', '"', '\n']):
                return '"' + value.replace('"', '""') + '"'
            return value

        csv_lines = []
        for row in values:
            csv_lines.append(",".join(escape_csv(v) for v in row))

        logger.info(f"CSV export: {range_name} rows={len(values)}")
        return "CSV Export:\n" + "\n".join(csv_lines)
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        return f"❌ Error exporting CSV: {str(e)}"

def sheet_find_replace_handler(
    spreadsheet_id: str,
    range_name: str,
    find_text: str,
    replace_text: str,
    dry_run: bool = True,
    match_case: bool = False
) -> str:
    """Find/replace in a range with dry-run preview"""
    try:
        if not find_text:
            return "❌ find_text is required."

        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)

        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()
        values = result.get('values', [])

        if not values:
            return "No data found."

        matches = []
        updated = []

        for r, row in enumerate(values):
            new_row = list(row)
            row_changed = False
            for c, cell in enumerate(row):
                if cell is None:
                    continue
                cell_str = str(cell)
                hay = cell_str if match_case else cell_str.lower()
                needle = find_text if match_case else find_text.lower()
                if needle in hay:
                    row_changed = True
                    new_value = cell_str.replace(find_text, replace_text) if match_case else _replace_ci(cell_str, find_text, replace_text)
                    new_row[c] = new_value
                    matches.append((r + 1, c + 1, cell_str, new_value))
            if row_changed:
                updated.append(new_row)
            else:
                updated.append(row)

        if dry_run:
            preview = matches[:20]
            output = f"🔍 DRY RUN: Found {len(matches)} matches\\n"
            if preview:
                output += "Preview (row, col, before → after):\\n"
                for r, c, before, after in preview:
                    output += f"- ({r}, {c}) {before} → {after}\\n"
            output += "To apply changes, call again with dry_run=False"
            logger.info(f"Find/replace dry-run: {range_name} matches={len(matches)}")
            return output

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={"values": updated}
        ).execute()

        logger.info(f"Find/replace applied: {range_name} matches={len(matches)}")
        return f"✅ Replaced {len(matches)} occurrence(s)."
    except Exception as e:
        logger.error(f"Error in find/replace: {str(e)}")
        return f"❌ Error in find/replace: {str(e)}"

def _replace_ci(text: str, find_text: str, replace_text: str) -> str:
    """Case-insensitive replace preserving original casing where possible"""
    pattern = re.compile(re.escape(find_text), re.IGNORECASE)
    return pattern.sub(replace_text, text)

def sheet_create_named_range_handler(
    spreadsheet_id: str,
    name: str,
    sheet_id: int,
    start_row: int,
    end_row: int,
    start_col: int,
    end_col: int
) -> str:
    """Create a named range in a spreadsheet using grid indexes"""
    try:
        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)

        requests = [{
            "addNamedRange": {
                "namedRange": {
                    "name": name,
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": start_row,
                        "endRowIndex": end_row,
                        "startColumnIndex": start_col,
                        "endColumnIndex": end_col
                    }
                }
            }
        }]

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests}
        ).execute()

        logger.info(f"Named range created: {name} sheet={sheet_id}")
        return f"✅ Named range created: {name}"
    except Exception as e:
        logger.error(f"Error creating named range: {str(e)}")
        return f"❌ Error creating named range: {str(e)}"

def get_spreadsheet_meta_handler(spreadsheet_id: str) -> str:
    try:
        creds = get_creds()
        service = build('sheets', 'v4', credentials=creds)
        
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        properties = sheet_metadata.get('properties', {})
        sheets = sheet_metadata.get('sheets', [])
        
        output = f"Spreadsheet: {properties.get('title')} (ID: {spreadsheet_id})\nSheets:\n"
        for sheet in sheets:
            props = sheet.get('properties', {})
            output += f"- {props.get('title')} (ID: {props.get('sheetId')})\n"
            
        return output
    except Exception as e:
        return f"Error getting metadata: {str(e)}"

# --- Gmail Handlers ---
def create_message(to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = "me"
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}

def send_email_handler(to: str, subject: str, body_text: str, draft_mode: bool = True) -> str:
    """Send email with draft mode by default for safety"""
    try:
        # Validate email
        if not validate_email(to):
            return f"❌ Invalid email format: {to}"
        
        creds = get_creds()
        service = build('gmail', 'v1', credentials=creds)
        message = create_message(to, subject, body_text)
        
        if draft_mode:
            # Create draft instead of sending
            draft = {'message': message}
            created_draft = service.users().drafts().create(userId="me", body=draft).execute()
            draft_id = created_draft['id']
            
            logger.info(f"Email draft created: {draft_id} to {to}")
            return (
                f"📝 EMAIL DRAFT CREATED (ID: {draft_id})\n\n"
                f"To: {to}\n"
                f"Subject: {subject}\n"
                f"Body: {body_text[:100]}{'...' if len(body_text) > 100 else ''}\n\n"
                f"⚠️ Email saved as DRAFT, not sent yet.\n\n"
                f"To send: send_email(..., draft_mode=False)\n"
                f"Or send draft: send_draft(draft_id='{draft_id}')"
            )
        
        # Actually send email
        sent_message = service.users().messages().send(userId="me", body=message).execute()
        logger.info(f"Email sent: {sent_message['id']} to {to}")
        return f"✅ Email sent. Message Id: {sent_message['id']}"
        
    except Exception as e:
        logger.error(f"Error sending email to {to}: {str(e)}")
        return f"❌ Error sending email: {str(e)}"

def send_draft_handler(draft_id: str) -> str:
    """Send an existing draft"""
    try:
        creds = get_creds()
        service = build('gmail', 'v1', credentials=creds)
        
        sent_message = service.users().drafts().send(
            userId="me", body={'id': draft_id}
        ).execute()
        
        logger.info(f"Draft sent: {draft_id}")
        return f"✅ Draft sent successfully. Message Id: {sent_message['id']}"
        
    except Exception as e:
        logger.error(f"Error sending draft {draft_id}: {str(e)}")
        return f"❌ Error sending draft: {str(e)}"

def get_gmail_profile_handler() -> str:
    """Get the authenticated Gmail address (profile)"""
    try:
        creds = get_creds()
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress', 'Unknown')
        logger.info(f"Gmail profile accessed: {email_address}")
        return f"✅ Authenticated Gmail address: {email_address}"
    except Exception as e:
        logger.error(f"Error getting Gmail profile: {str(e)}")
        return f"❌ Error getting Gmail profile: {str(e)}"

def create_draft_handler(to: str, subject: str, body_text: str) -> str:
    try:
        creds = get_creds()
        service = build('gmail', 'v1', credentials=creds)
        
        message = create_message(to, subject, body_text)
        draft = {'message': message}
        created_draft = service.users().drafts().create(userId="me", body=draft).execute()
        
        return f"Draft created. Draft Id: {created_draft['id']}"
    except Exception as e:
        return f"Error creating draft: {str(e)}"

def list_emails_handler(max_results: int = 10, query: str = None) -> str:
    try:
        creds = get_creds()
        service = build('gmail', 'v1', credentials=creds)
        
        q = query if query else ""
        results = service.users().messages().list(userId='me', maxResults=max_results, q=q).execute()
        messages = results.get('messages', [])
        
        if not messages:
            return "No messages found."
            
        output = "Messages:\n"
        for msg in messages:
            # Get minimal details for the list
            txt = service.users().messages().get(userId='me', id=msg['id'], format='minimal').execute()
            snippet = txt.get('snippet', '')
            output += f"- ID: {msg['id']} | Snippet: {snippet}\n"
            
        return output
    except Exception as e:
        return f"Error listing emails: {str(e)}"

def read_email_handler(message_id: str) -> str:
    try:
        creds = get_creds()
        service = build('gmail', 'v1', credentials=creds)
        
        message = service.users().messages().get(userId='me', id=message_id).execute()
        
        payload = message.get('payload', {})
        headers = payload.get('headers', [])
        
        subject = ""
        sender = ""
        for header in headers:
            if header['name'] == 'Subject':
                subject = header['value']
            if header['name'] == 'From':
                sender = header['value']
                
        snippet = message.get('snippet', '')
        
        # Simplified body retrieval (just snippet for now to be safe, or full text if needed)
        # Getting full body is complex due to multipart/alternative structure
        
        return f"From: {sender}\nSubject: {subject}\nSnippet: {snippet}\n"
    except Exception as e:
        return f"Error reading email: {str(e)}"

def delete_email_handler(message_id: str, confirm: bool = False) -> str:
    """Delete email with confirmation requirement"""
    try:
        creds = get_creds()
        service = build('gmail', 'v1', credentials=creds)
        
        # Get email preview for confirmation message
        try:
            msg = service.users().messages().get(
                userId='me', id=message_id, format='minimal'
            ).execute()
            snippet = msg.get('snippet', 'No preview available')[:100]
        except:
            snippet = 'Unable to load preview'
        
        if not confirm:
            logger.warning(f"Delete email attempted without confirm: {message_id}")
            return (
                f"⚠️ CONFIRMATION REQUIRED\n\n"
                f"This will permanently delete email {message_id}.\n\n"
                f"Email preview:\n{snippet}...\n\n"
                f"⚠️ To proceed, call this tool again with confirm=True"
            )
        
        # Delete email
        service.users().messages().delete(userId='me', id=message_id).execute()
        logger.info(f"Email deleted: {message_id}")
        return f"✅ Email {message_id} deleted successfully."
        
    except Exception as e:
        logger.error(f"Error deleting email {message_id}: {str(e)}")
        return f"❌ Error deleting email: {str(e)}"

def batch_delete_emails_handler(message_ids: List[str], dry_run: bool = True) -> str:
    """Batch delete emails with dry-run mode"""
    try:
        creds = get_creds()
        service = build('gmail', 'v1', credentials=creds)
        
        if dry_run:
            # Preview mode - show what will be deleted
            preview = f"🔍 DRY RUN MODE - No emails will be deleted\n\n"
            preview += f"Would delete {len(message_ids)} email(s):\n\n"
            
            # Load previews for first 10 emails
            previews_to_show = min(10, len(message_ids))
            for i, msg_id in enumerate(message_ids[:previews_to_show]):
                try:
                    msg = service.users().messages().get(
                        userId='me', id=msg_id, format='minimal'
                    ).execute()
                    snippet = msg.get('snippet', 'No preview')[:80]
                    preview += f"  • {msg_id}: {snippet}...\n"
                except:
                    preview += f"  • {msg_id}: (unable to load preview)\n"
            
            if len(message_ids) > previews_to_show:
                preview += f"\n... and {len(message_ids) - previews_to_show} more\n"
            
            preview += f"\n⚠️ To actually delete these emails, call with dry_run=False"
            logger.info(f"Batch delete dry-run: {len(message_ids)} emails")
            return preview
        
        # Real deletion
        body = {'ids': message_ids}
        service.users().messages().batchDelete(userId='me', body=body).execute()
        logger.info(f"Batch deleted {len(message_ids)} emails")
        return f"✅ Successfully deleted {len(message_ids)} email(s)."
        
    except Exception as e:
        logger.error(f"Error batch deleting emails: {str(e)}")
        return f"❌ Error batch deleting emails: {str(e)}"

def gmail_search_and_summarize_handler(query: str, max_results: int = 50) -> str:
    """Search Gmail and return a brief summary"""
    try:
        creds = get_creds()
        service = build('gmail', 'v1', credentials=creds)

        if not query:
            return "❌ Query is required."

        results = service.users().messages().list(
            userId='me', maxResults=min(max_results, 100), q=query
        ).execute()
        messages = results.get('messages', [])

        if not messages:
            return "No messages found."

        summary_lines = []
        for msg in messages[:min(len(messages), 20)]:
            full = service.users().messages().get(
                userId='me', id=msg['id'], format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            headers = {h['name']: h['value'] for h in full.get('payload', {}).get('headers', [])}
            summary_lines.append(
                f"- {headers.get('Date','')} | {headers.get('From','')} | {headers.get('Subject','')}"
            )

        logger.info(f"Gmail search: query='{query}' results={len(messages)}")
        output = f"Found {len(messages)} message(s) for query: {query}\n"
        output += "Top results:\n" + "\n".join(summary_lines)
        return output
    except Exception as e:
        logger.error(f"Error searching Gmail: {str(e)}")
        return f"❌ Error searching Gmail: {str(e)}"

def gmail_archive_handler(message_id: str, confirm: bool = False) -> str:
    """Archive a Gmail message (remove INBOX label)"""
    try:
        if not confirm:
            return (
                "⚠️ CONFIRMATION REQUIRED\n\n"
                f"This will archive message {message_id} (remove from INBOX).\n"
                "To proceed, call again with confirm=True."
            )

        creds = get_creds()
        service = build('gmail', 'v1', credentials=creds)

        service.users().messages().modify(
            userId='me', id=message_id, body={"removeLabelIds": ["INBOX"]}
        ).execute()

        logger.info(f"Gmail archived: {message_id}")
        return f"✅ Message archived: {message_id}"
    except Exception as e:
        logger.error(f"Error archiving message {message_id}: {str(e)}")
        return f"❌ Error archiving message: {str(e)}"

def _get_or_create_label_id(service, label_name: str, create_if_missing: bool = True) -> str:
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    for lbl in labels:
        if lbl.get('name') == label_name:
            return lbl.get('id')
    if not create_if_missing:
        return None
    created = service.users().labels().create(
        userId='me',
        body={"name": label_name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
    ).execute()
    return created.get('id')

def gmail_label_apply_handler(
    message_ids: List[str],
    label_name: str,
    dry_run: bool = True,
    create_if_missing: bool = True
) -> str:
    """Apply a label to messages with dry-run preview"""
    try:
        if not message_ids:
            return "❌ message_ids is required."
        if not label_name:
            return "❌ label_name is required."

        creds = get_creds()
        service = build('gmail', 'v1', credentials=creds)
        label_id = _get_or_create_label_id(service, label_name, create_if_missing)
        if not label_id:
            return f"❌ Label not found: {label_name}"

        if dry_run:
            preview_ids = message_ids[:10]
            logger.info(f"Gmail label dry-run: {label_name} count={len(message_ids)}")
            return (
                f"🔍 DRY RUN: Would apply label '{label_name}' to {len(message_ids)} message(s).\n"
                f"Sample IDs: {', '.join(preview_ids)}\n"
                "To apply, call again with dry_run=False."
            )

        for mid in message_ids:
            service.users().messages().modify(
                userId='me', id=mid, body={"addLabelIds": [label_id]}
            ).execute()

        logger.info(f"Gmail label applied: {label_name} count={len(message_ids)}")
        return f"✅ Label '{label_name}' applied to {len(message_ids)} message(s)."
    except Exception as e:
        logger.error(f"Error applying label: {str(e)}")
        return f"❌ Error applying label: {str(e)}"

# --- Google Calendar Handlers ---
def list_events_handler(calendar_id: str = 'primary', max_results: int = 10) -> str:
    try:
        creds = get_creds()
        service = build('calendar', 'v3', credentials=creds)
        
        events_result = service.events().list(calendarId=calendar_id, maxResults=max_results, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            return 'No upcoming events found.'
            
        output = "Upcoming events:\n"
        for event in events:
            start = event.get('start').get('dateTime', event.get('start').get('date'))
            output += f"- {start} : {event.get('summary')} (ID: {event.get('id')})\n"
            
        return output
    except Exception as e:
        return f"Error listing events: {str(e)}"

def create_event_handler(summary: str, start_time: str, end_time: str, description: str = "") -> str:
    try:
        creds = get_creds()
        service = build('calendar', 'v3', credentials=creds)
        
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
        }
        
        event = service.events().insert(calendarId='primary', body=event).execute()
        return f"Event created: {event.get('htmlLink')}"
    except Exception as e:
        return f"Error creating event: {str(e)}"

def calendar_find_free_slots_handler(
    calendar_id: str,
    start_time: str,
    end_time: str,
    duration_minutes: int = 30,
    max_results: int = 5
) -> str:
    """Find free time slots in a calendar between start and end"""
    try:
        creds = get_creds()
        service = build('calendar', 'v3', credentials=creds)

        time_min = start_time
        time_max = end_time

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        def to_dt(dt):
            if not dt:
                return None
            return datetime.fromisoformat(dt.replace('Z', '+00:00'))

        start_dt = to_dt(start_time)
        end_dt = to_dt(end_time)
        if not start_dt or not end_dt:
            return "❌ Invalid start_time or end_time."

        busy = []
        for event in events:
            s = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
            e = event.get('end', {}).get('dateTime') or event.get('end', {}).get('date')
            s_dt = to_dt(s if 'T' in str(s) else f"{s}T00:00:00+00:00")
            e_dt = to_dt(e if 'T' in str(e) else f"{e}T00:00:00+00:00")
            if s_dt and e_dt:
                busy.append((s_dt, e_dt))

        busy.sort(key=lambda x: x[0])

        slots = []
        cursor = start_dt
        duration = timedelta(minutes=duration_minutes)

        for s_dt, e_dt in busy:
            if cursor + duration <= s_dt:
                slots.append((cursor, s_dt))
                if len(slots) >= max_results:
                    break
            if e_dt > cursor:
                cursor = e_dt

        if len(slots) < max_results and cursor + duration <= end_dt:
            slots.append((cursor, end_dt))

        if not slots:
            return "No free slots found."

        output = f"Free slots (duration {duration_minutes} min):\n"
        for s_dt, e_dt in slots[:max_results]:
            output += f"- {s_dt.isoformat()} to {e_dt.isoformat()}\n"

        logger.info(f"Free slots found: {len(slots)} between {start_time} and {end_time}")
        return output
    except Exception as e:
        logger.error(f"Error finding free slots: {str(e)}")
        return f"❌ Error finding free slots: {str(e)}"

def calendar_create_meeting_handler(
    summary: str,
    start_time: str,
    end_time: str,
    attendees: List[str] = None,
    description: str = "",
    location: str = "",
    confirm: bool = False
) -> str:
    """Create a calendar meeting with attendees (confirm required)"""
    try:
        if not confirm:
            return (
                "⚠️ CONFIRMATION REQUIRED\n\n"
                "This will create a calendar event and invite attendees.\n"
                "To proceed, call again with confirm=True."
            )

        creds = get_creds()
        service = build('calendar', 'v3', credentials=creds)

        event = {
            'summary': summary,
            'description': description,
            'location': location,
            'start': {'dateTime': start_time, 'timeZone': 'UTC'},
            'end': {'dateTime': end_time, 'timeZone': 'UTC'}
        }
        if attendees:
            event['attendees'] = [{'email': a} for a in attendees if validate_email(a)]

        created = service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
        logger.info(f"Meeting created: {created.get('id')}")
        return f"✅ Meeting created: {created.get('htmlLink')}"
    except Exception as e:
        logger.error(f"Error creating meeting: {str(e)}")
        return f"❌ Error creating meeting: {str(e)}"

# --- Google Drive Handlers ---
def create_folder_handler(name: str, parent_id: str = None) -> str:
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
            
        file = service.files().create(body=file_metadata, fields='id').execute()
        return f"Folder created: {name} (ID: {file.get('id')})"
    except Exception as e:
        return f"Error creating folder: {str(e)}"

def move_file_handler(file_id: str, folder_id: str) -> str:
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        
        # Retrieve the existing parents to remove
        file = service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents'))
        
        # Move the file to the new folder
        file = service.files().update(fileId=file_id, addParents=folder_id,
                                      removeParents=previous_parents,
                                      fields='id, parents').execute()
        return f"File moved to folder ID {folder_id}."
    except Exception as e:
        return f"Error moving file: {str(e)}"

def share_file_handler(file_id: str, role: str, type: str = 'user', 
                       email_address: str = None, allow_public: bool = False) -> str:
    """Share file with public access protection"""
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        
        # Block public sharing without explicit confirmation
        if type == 'anyone' and not allow_public:
            # Get file info
            try:
                file_info = service.files().get(
                    fileId=file_id, 
                    fields='name,size,mimeType,owners'
                ).execute()
                file_name = file_info.get('name', 'Unknown')
                file_size = int(file_info.get('size', 0)) / (1024 * 1024)  # MB
            except:
                file_name = 'Unknown'
                file_size = 0
            
            logger.warning(f"Public sharing blocked for file: {file_id}")
            return (
                f"⚠️ PUBLIC ACCESS BLOCKED\n\n"
                f"You are trying to make this file PUBLIC:\n"
                f"  📄 {file_name}\n"
                f"  📊 Size: {file_size:.2f} MB\n"
                f"  🔗 Will be accessible to: ANYONE with the link\n\n"
                f"⚠️ SECURITY WARNING:\n"
                f"  • File may be indexed by search engines\n"
                f"  • Anyone can view, download and share it\n"
                f"  • You cannot track who accessed it\n\n"
                f"To proceed, you must explicitly set allow_public=True\n\n"
                f"✅ Safer alternative: Share with specific users using type='user'"
            )
        
        # Validate email if type is user/group
        if type in ['user', 'group'] and email_address:
            if not validate_email(email_address):
                return f"❌ Invalid email format: {email_address}"
        
        permission = {
            'type': type,
            'role': role,
        }
        if email_address:
            permission['emailAddress'] = email_address
            
        service.permissions().create(fileId=file_id, body=permission).execute()
        
        log_msg = f"File shared: {file_id} ({type}={email_address or 'anyone'}, role={role})"
        logger.info(log_msg)
        
        result = f"✅ File shared successfully\n\n"
        result += f"📄 File ID: {file_id}\n"
        result += f"🌐 Access: {type}\n"
        result += f"👤 Role: {role}\n"
        
        if type == 'anyone':
            result += f"\n⚠️ This file is now PUBLIC"
        
        return result
        
    except Exception as e:
        logger.error(f"Error sharing file {file_id}: {str(e)}")
        return f"❌ Error sharing file: {str(e)}"

def drive_search_advanced_handler(query: str, limit: int = 50) -> str:
    """Advanced Drive search with query and limit"""
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)

        if not query:
            return "❌ Query is required."

        results = service.files().list(
            q=query,
            pageSize=min(max(limit, 1), 100),
            fields="files(id, name, mimeType, owners, modifiedTime)"
        ).execute()

        items = results.get('files', [])
        if not items:
            return "No files found."

        output = "Found files:\n"
        for item in items:
            owners = item.get('owners', [])
            owner = owners[0].get('emailAddress') if owners else 'Unknown'
            output += (
                f"- {item.get('name')} (ID: {item.get('id')}) "
                f"[{item.get('mimeType')}] owner={owner} "
                f"modified={item.get('modifiedTime')}\n"
            )

        logger.info(f"Drive search: query='{query}' results={len(items)}")
        return output
    except Exception as e:
        logger.error(f"Error searching files (advanced): {str(e)}")
        return f"Error searching files: {str(e)}"

def drive_list_permissions_handler(file_id: str) -> str:
    """List permissions for a Drive file"""
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)

        perms = service.permissions().list(
            fileId=file_id,
            fields="permissions(id,type,role,emailAddress,domain,allowFileDiscovery)"
        ).execute()

        items = perms.get('permissions', [])
        if not items:
            return "No permissions found."

        output = f"Permissions for file {file_id}:\n"
        for p in items:
            target = p.get('emailAddress') or p.get('domain') or 'anyone'
            output += (
                f"- id={p.get('id')} type={p.get('type')} "
                f"role={p.get('role')} target={target}\n"
            )

        logger.info(f"Drive permissions listed: {file_id} count={len(items)}")
        return output
    except Exception as e:
        logger.error(f"Error listing permissions for {file_id}: {str(e)}")
        return f"Error listing permissions: {str(e)}"

def drive_revoke_public_handler(file_id: str, confirm: bool = False) -> str:
    """Revoke public access (type=anyone) for a Drive file"""
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)

        perms = service.permissions().list(
            fileId=file_id,
            fields="permissions(id,type,role,allowFileDiscovery)"
        ).execute()
        items = perms.get('permissions', [])
        public_perms = [p for p in items if p.get('type') == 'anyone']

        if not public_perms:
            return "No public permissions found."

        if not confirm:
            return (
                f"⚠️ CONFIRMATION REQUIRED\n\n"
                f"Public access permissions found: {len(public_perms)}\n"
                f"To revoke, call again with confirm=True."
            )

        for p in public_perms:
            service.permissions().delete(fileId=file_id, permissionId=p.get('id')).execute()

        logger.info(f"Public access revoked: {file_id} count={len(public_perms)}")
        return f"✅ Public access revoked for file {file_id}."
    except Exception as e:
        logger.error(f"Error revoking public access for {file_id}: {str(e)}")
        return f"Error revoking public access: {str(e)}"

def drive_copy_file_handler(file_id: str, name: str = None, parent_id: str = None) -> str:
    """Copy a Drive file to a new file"""
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)

        body = {}
        if name:
            body['name'] = name
        if parent_id:
            body['parents'] = [parent_id]

        copied = service.files().copy(fileId=file_id, body=body, fields="id,name").execute()
        logger.info(f"File copied: {file_id} -> {copied.get('id')}")
        return f"✅ File copied: {copied.get('name')} (ID: {copied.get('id')})"
    except Exception as e:
        logger.error(f"Error copying file {file_id}: {str(e)}")
        return f"Error copying file: {str(e)}"

# Server Setup
server = Server("My Google Tools")

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="find_files",
            description="Search for files on Google Drive. Query example: 'name contains \"System\"'",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="read_sheet",
            description="Read data from a Google Sheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "range_name": {"type": "string"}
                },
                "required": ["spreadsheet_id", "range_name"]
            }
        ),
        types.Tool(
            name="append_row",
            description="Append a row to a Google Sheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "range_name": {"type": "string"},
                    "values": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["spreadsheet_id", "range_name", "values"]
            }
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
                        "items": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "required": ["spreadsheet_id", "range_name", "values"]
            }
        ),
        types.Tool(
            name="create_script_project",
            description="Create a new Google Apps Script project",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "parent_id": {"type": "string"}
                },
                "required": ["title"]
            }
        ),
        types.Tool(
            name="get_script_content",
            description="Get the content of a Google Apps Script project",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_id": {"type": "string"}
                },
                "required": ["script_id"]
            }
        ),
        types.Tool(
            name="prepare_script_update",
            description="STEP 1: Prepare a Google Apps Script update with automatic backup. Returns operation_id.",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_id": {
                        "type": "string",
                        "description": "The Apps Script project ID"
                    },
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "source": {"type": "string"}
                            },
                            "required": ["name", "type", "source"]
                        },
                        "description": "Array of files to update"
                    }
                },
                "required": ["script_id", "files"]
            }
        ),
        types.Tool(
            name="execute_operation",
            description="STEP 2: Execute a prepared operation by operation_id (from prepare_script_update)",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation_id": {
                        "type": "string",
                        "description": "The operation ID from prepare_script_update"
                    }
                },
                "required": ["operation_id"]
            }
        ),
        types.Tool(
            name="cancel_operation",
            description="Cancel a prepared operation before execution",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation_id": {
                        "type": "string",
                        "description": "The operation ID to cancel"
                    }
                },
                "required": ["operation_id"]
            }
        ),
        types.Tool(
            name="restore_script_backup",
            description="Restore a script from a backup file",
            inputSchema={
                "type": "object",
                "properties": {
                    "backup_path": {
                        "type": "string",
                        "description": "Full path to the backup JSON file"
                    }
                },
                "required": ["backup_path"]
            }
        ),
        # --- New Tools ---
        types.Tool(
            name="read_doc",
            description="Read the content of a Google Doc",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string"}
                },
                "required": ["document_id"]
            }
        ),
        types.Tool(
            name="create_doc",
            description="Create a new Google Doc",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"}
                },
                "required": ["title"]
            }
        ),
        types.Tool(
            name="append_to_doc",
            description="Append text to a Google Doc",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string"},
                    "text": {"type": "string"}
                },
                "required": ["document_id", "text"]
            }
        ),
        types.Tool(
            name="doc_fill_template",
            description="Fill a Google Doc template by replacing placeholders. Requires confirm=True.",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string"},
                    "replacements": {"type": "object"},
                    "confirm": {"type": "boolean", "default": False}
                },
                "required": ["document_id", "replacements"]
            }
        ),
        types.Tool(
            name="doc_export_pdf",
            description="Export a Google Doc to PDF (base64)",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string"}
                },
                "required": ["document_id"]
            }
        ),
        types.Tool(
            name="create_spreadsheet",
            description="Create a new Google Spreadsheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"}
                },
                "required": ["title"]
            }
        ),
        types.Tool(
            name="add_sheet",
            description="Add a new sheet (tab) to a spreadsheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "title": {"type": "string"}
                },
                "required": ["spreadsheet_id", "title"]
            }
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
                        "default": False
                    }
                },
                "required": ["spreadsheet_id", "range_name"]
            }
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
                    "end_col": {"type": "integer"}
                },
                "required": ["spreadsheet_id", "sheet_id", "title"]
            }
        ),
        types.Tool(
            name="sheet_export_csv",
            description="Export a range as CSV text",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "range_name": {"type": "string"},
                    "max_rows": {"type": "integer", "default": 5000}
                },
                "required": ["spreadsheet_id", "range_name"]
            }
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
                    "match_case": {"type": "boolean", "default": False}
                },
                "required": ["spreadsheet_id", "range_name", "find_text", "replace_text"]
            }
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
                    "end_col": {"type": "integer"}
                },
                "required": ["spreadsheet_id", "name", "sheet_id", "start_row", "end_row", "start_col", "end_col"]
            }
        ),
        types.Tool(
            name="get_spreadsheet_meta",
            description="Get metadata (sheets, titles) of a spreadsheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"}
                },
                "required": ["spreadsheet_id"]
            }
        ),
        types.Tool(
            name="send_email",
            description="Send an email via Gmail. Defaults to draft_mode=True for safety!",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {"type": "string"},
                    "body_text": {"type": "string"},
                    "draft_mode": {
                        "type": "boolean",
                        "description": "If true (default), creates draft instead of sending. Set to false to actually send.",
                        "default": True
                    }
                },
                "required": ["to", "subject", "body_text"]
            }
        ),
        types.Tool(
            name="send_draft",
            description="Send an existing draft email by draft ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "draft_id": {
                        "type": "string",
                        "description": "The ID of the draft to send"
                    }
                },
                "required": ["draft_id"]
            }
        ),
        types.Tool(
            name="get_gmail_profile",
            description="Get the authenticated Gmail address for the current OAuth token",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="create_draft",
            description="Create a draft email in Gmail",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body_text": {"type": "string"}
                },
                "required": ["to", "subject", "body_text"]
            }
        ),
        types.Tool(
            name="list_emails",
            description="List emails from Gmail",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {"type": "integer"},
                    "query": {"type": "string", "description": "Gmail search query (e.g. 'is:unread')"}
                }
            }
        ),
        types.Tool(
            name="read_email",
            description="Read a specific email by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string"}
                },
                "required": ["message_id"]
            }
        ),
        types.Tool(
            name="delete_email",
            description="Delete a specific email by ID. REQUIRES confirm=True parameter for safety!",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "The ID of the email to delete"
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "MUST be true to actually delete the email. Safety check.",
                        "default": False
                    }
                },
                "required": ["message_id", "confirm"]
            }
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
                        "description": "List of message IDs to delete"
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true (default), shows preview without deleting. Set to false to actually delete.",
                        "default": True
                    }
                },
                "required": ["message_ids"]
            }
        ),
        types.Tool(
            name="gmail_search_and_summarize",
            description="Search Gmail and return a brief summary",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 50}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="gmail_archive",
            description="Archive a Gmail message (remove INBOX). Requires confirm=True.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string"},
                    "confirm": {"type": "boolean", "default": False}
                },
                "required": ["message_id"]
            }
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
                    "create_if_missing": {"type": "boolean", "default": True}
                },
                "required": ["message_ids", "label_name"]
            }
        ),
        types.Tool(
            name="list_events",
            description="List upcoming calendar events",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string"},
                    "max_results": {"type": "integer"}
                }
            }
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
                    "description": {"type": "string"}
                },
                "required": ["summary", "start_time", "end_time"]
            }
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
                    "max_results": {"type": "integer", "default": 5}
                },
                "required": ["start_time", "end_time"]
            }
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
                    "confirm": {"type": "boolean", "default": False}
                },
                "required": ["summary", "start_time", "end_time"]
            }
        ),
        types.Tool(
            name="create_folder",
            description="Create a folder in Google Drive",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "parent_id": {"type": "string"}
                },
                "required": ["name"]
            }
        ),
        types.Tool(
            name="move_file",
            description="Move a file to a different folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {"type": "string"},
                    "folder_id": {"type": "string"}
                },
                "required": ["file_id", "folder_id"]
            }
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
                        "description": "Access type. 'anyone' requires allow_public=True"
                    },
                    "email_address": {
                        "type": "string",
                        "description": "Required for type 'user' or 'group'"
                    },
                    "allow_public": {
                        "type": "boolean",
                        "description": "MUST be true to share with type='anyone'. Security check.",
                        "default": False
                    }
                },
                "required": ["file_id", "role"]
            }
        ),
        types.Tool(
            name="drive_search_advanced",
            description="Advanced Google Drive search with full query syntax",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 50}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="drive_list_permissions",
            description="List permissions for a Drive file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {"type": "string"}
                },
                "required": ["file_id"]
            }
        ),
        types.Tool(
            name="drive_revoke_public",
            description="Revoke public access (type=anyone) for a Drive file. Requires confirm=True.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {"type": "string"},
                    "confirm": {"type": "boolean", "default": False}
                },
                "required": ["file_id"]
            }
        ),
        types.Tool(
            name="drive_copy_file",
            description="Copy a Drive file to a new file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {"type": "string"},
                    "name": {"type": "string"},
                    "parent_id": {"type": "string"}
                },
                "required": ["file_id"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if not arguments:
        arguments = {}

    try:
        require_auth(arguments)
        if name == "find_files":
            result = find_files_handler(arguments.get("query"))
        elif name == "read_sheet":
            result = read_sheet_handler(arguments.get("spreadsheet_id"), arguments.get("range_name"))
        elif name == "append_row":
            result = append_row_handler(arguments.get("spreadsheet_id"), arguments.get("range_name"), arguments.get("values"))
        elif name == "update_sheet":
            result = update_sheet_handler(arguments.get("spreadsheet_id"), arguments.get("range_name"), arguments.get("values"))
        elif name == "create_script_project":
            result = create_script_project_handler(arguments.get("title"), arguments.get("parent_id"))
        elif name == "get_script_content":
            result = get_script_content_handler(arguments.get("script_id"))
        elif name == "prepare_script_update":
            result = prepare_script_update_handler(arguments.get("script_id"), arguments.get("files"))
        elif name == "execute_operation":
            result = execute_operation_handler(arguments.get("operation_id"))
        elif name == "cancel_operation":
            result = cancel_operation_handler(arguments.get("operation_id"))
        elif name == "restore_script_backup":
            result = restore_script_backup_handler(arguments.get("backup_path"))
        # --- New Tools Routing ---
        elif name == "read_doc":
            result = read_doc_handler(arguments.get("document_id"))
        elif name == "create_doc":
            result = create_doc_handler(arguments.get("title"))
        elif name == "append_to_doc":
            result = append_to_doc_handler(arguments.get("document_id"), arguments.get("text"))
        elif name == "doc_fill_template":
            result = doc_fill_template_handler(
                arguments.get("document_id"),
                arguments.get("replacements"),
                arguments.get("confirm", False)
            )
        elif name == "doc_export_pdf":
            result = doc_export_pdf_handler(arguments.get("document_id"))
        elif name == "create_spreadsheet":
            result = create_spreadsheet_handler(arguments.get("title"))
        elif name == "add_sheet":
            result = add_sheet_handler(arguments.get("spreadsheet_id"), arguments.get("title"))
        elif name == "clear_range":
            result = clear_range_handler(arguments.get("spreadsheet_id"), arguments.get("range_name"), arguments.get("confirm", False))
        elif name == "sheet_create_filter_view":
            result = sheet_create_filter_view_handler(
                arguments.get("spreadsheet_id"),
                arguments.get("sheet_id"),
                arguments.get("title"),
                arguments.get("start_row", 0),
                arguments.get("end_row"),
                arguments.get("start_col", 0),
                arguments.get("end_col")
            )
        elif name == "sheet_export_csv":
            result = sheet_export_csv_handler(
                arguments.get("spreadsheet_id"),
                arguments.get("range_name"),
                arguments.get("max_rows", 5000)
            )
        elif name == "sheet_find_replace":
            result = sheet_find_replace_handler(
                arguments.get("spreadsheet_id"),
                arguments.get("range_name"),
                arguments.get("find_text"),
                arguments.get("replace_text"),
                arguments.get("dry_run", True),
                arguments.get("match_case", False)
            )
        elif name == "sheet_create_named_range":
            result = sheet_create_named_range_handler(
                arguments.get("spreadsheet_id"),
                arguments.get("name"),
                arguments.get("sheet_id"),
                arguments.get("start_row"),
                arguments.get("end_row"),
                arguments.get("start_col"),
                arguments.get("end_col")
            )
        elif name == "get_spreadsheet_meta":
            result = get_spreadsheet_meta_handler(arguments.get("spreadsheet_id"))
        elif name == "send_email":
            result = send_email_handler(arguments.get("to"), arguments.get("subject"), arguments.get("body_text"), arguments.get("draft_mode", True))
        elif name == "send_draft":
            result = send_draft_handler(arguments.get("draft_id"))
        elif name == "get_gmail_profile":
            result = get_gmail_profile_handler()
        elif name == "create_draft":
            result = create_draft_handler(arguments.get("to"), arguments.get("subject"), arguments.get("body_text"))
        elif name == "list_emails":
            result = list_emails_handler(arguments.get("max_results", 10), arguments.get("query"))
        elif name == "read_email":
            result = read_email_handler(arguments.get("message_id"))
        elif name == "delete_email":
            result = delete_email_handler(arguments.get("message_id"), arguments.get("confirm", False))
        elif name == "batch_delete_emails":
            result = batch_delete_emails_handler(arguments.get("message_ids"), arguments.get("dry_run", True))
        elif name == "gmail_search_and_summarize":
            result = gmail_search_and_summarize_handler(arguments.get("query"), arguments.get("max_results", 50))
        elif name == "gmail_archive":
            result = gmail_archive_handler(arguments.get("message_id"), arguments.get("confirm", False))
        elif name == "gmail_label_apply":
            result = gmail_label_apply_handler(
                arguments.get("message_ids"),
                arguments.get("label_name"),
                arguments.get("dry_run", True),
                arguments.get("create_if_missing", True)
            )
        elif name == "list_events":
            result = list_events_handler(arguments.get("calendar_id", "primary"), arguments.get("max_results", 10))
        elif name == "create_event":
            result = create_event_handler(arguments.get("summary"), arguments.get("start_time"), arguments.get("end_time"), arguments.get("description", ""))
        elif name == "calendar_find_free_slots":
            result = calendar_find_free_slots_handler(
                arguments.get("calendar_id", "primary"),
                arguments.get("start_time"),
                arguments.get("end_time"),
                arguments.get("duration_minutes", 30),
                arguments.get("max_results", 5)
            )
        elif name == "calendar_create_meeting":
            result = calendar_create_meeting_handler(
                arguments.get("summary"),
                arguments.get("start_time"),
                arguments.get("end_time"),
                arguments.get("attendees"),
                arguments.get("description", ""),
                arguments.get("location", ""),
                arguments.get("confirm", False)
            )
        elif name == "create_folder":
            result = create_folder_handler(arguments.get("name"), arguments.get("parent_id"))
        elif name == "move_file":
            result = move_file_handler(arguments.get("file_id"), arguments.get("folder_id"))
        elif name == "share_file":
            result = share_file_handler(arguments.get("file_id"), arguments.get("role"), arguments.get("type", "user"), arguments.get("email_address"), arguments.get("allow_public", False))
        elif name == "drive_search_advanced":
            result = drive_search_advanced_handler(arguments.get("query"), arguments.get("limit", 50))
        elif name == "drive_list_permissions":
            result = drive_list_permissions_handler(arguments.get("file_id"))
        elif name == "drive_revoke_public":
            result = drive_revoke_public_handler(arguments.get("file_id"), arguments.get("confirm", False))
        elif name == "drive_copy_file":
            result = drive_copy_file_handler(arguments.get("file_id"), arguments.get("name"), arguments.get("parent_id"))
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(type="text", text=str(result))]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def run():
    async with stdio_server() as (read, write):
        await server.run(
            read_stream=read,
            write_stream=write,
            initialization_options=server.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
