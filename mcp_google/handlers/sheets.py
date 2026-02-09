import logging
import re
from typing import List, Optional

from googleapiclient.discovery import build

from ..auth import get_creds
from ..config import Config


def read_sheet_handler(config: Config, logger: logging.Logger, spreadsheet_id: str, range_name: str) -> str:
    try:
        creds = get_creds(config)
        service = build("sheets", "v4", credentials=creds)

        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()
        values = result.get("values", [])

        if not values:
            return "No data found."

        output = f"Data from sheet (range {range_name}):\n"
        for row in values:
            output += f"| {' | '.join(row)} |\n"

        return output
    except Exception as e:
        return f"Error reading sheet: {str(e)}"


def append_row_handler(
    config: Config, logger: logging.Logger, spreadsheet_id: str, range_name: str, values: List[str]
) -> str:
    try:
        creds = get_creds(config)
        service = build("sheets", "v4", credentials=creds)

        body = {"values": [values]}

        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )

        return (
            f"Successfully appended {result.get('updates').get('updatedCells')} cells."
        )
    except Exception as e:
        return f"Error appending row: {str(e)}"


def update_sheet_handler(
    config: Config,
    logger: logging.Logger,
    spreadsheet_id: str,
    range_name: str,
    values: List[List[str]],
) -> str:
    try:
        creds = get_creds(config)
        service = build("sheets", "v4", credentials=creds)

        body = {"values": values}

        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )

        return f"Successfully updated {result.get('updatedCells')} cells."
    except Exception as e:
        return f"Error updating sheet: {str(e)}"


def create_spreadsheet_handler(config: Config, logger: logging.Logger, title: str) -> str:
    try:
        creds = get_creds(config)
        service = build("sheets", "v4", credentials=creds)

        spreadsheet = {"properties": {"title": title}}
        spreadsheet = (
            service.spreadsheets()
            .create(body=spreadsheet, fields="spreadsheetId")
            .execute()
        )
        return f"Created spreadsheet with ID: {spreadsheet.get('spreadsheetId')}"
    except Exception as e:
        return f"Error creating spreadsheet: {str(e)}"


def add_sheet_handler(
    config: Config, logger: logging.Logger, spreadsheet_id: str, title: str
) -> str:
    try:
        creds = get_creds(config)
        service = build("sheets", "v4", credentials=creds)

        requests = [
            {
                "addSheet": {
                    "properties": {
                        "title": title,
                    }
                }
            }
        ]

        body = {"requests": requests}
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body=body
        ).execute()

        return f"Added sheet '{title}' to spreadsheet."
    except Exception as e:
        return f"Error adding sheet: {str(e)}"


def clear_range_handler(
    config: Config,
    logger: logging.Logger,
    spreadsheet_id: str,
    range_name: str,
    confirm: bool = False,
) -> str:
    """Clear range with auto dry-run for large ranges."""
    try:
        creds = get_creds(config)
        service = build("sheets", "v4", credentials=creds)

        # Analyze the range to decide whether confirmation is needed
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_name
            ).execute()
            values = result.get("values", [])

            rows = len(values)
            cols = max(len(row) for row in values) if values else 0
            total_cells = rows * cols
            filled_cells = sum(len(row) for row in values)
        except Exception:
            total_cells = 0
            filled_cells = 0

        # Auto dry-run for large ranges (>100 cells)
        if total_cells > 100 and not confirm:
            logger.warning(
                "Large range clear blocked: %s (%s cells)", range_name, total_cells
            )
            result = f"🔍 DRY RUN: Large range detected ({total_cells:,} cells)\n\n"
            result += f"Would clear range: {range_name}\n\n"
            result += "📊 Current data analysis:\n"
            result += f"  • Total cells: {total_cells:,}\n"
            result += f"  • Filled cells: {filled_cells:,} "
            result += f"({filled_cells/total_cells*100:.1f}%)\n"
            result += f"  • Empty cells: {total_cells-filled_cells:,}\n\n"
            result += (
                f"⚠️ WARNING: This will delete all data in {filled_cells:,} cells\n\n"
            )
            result += "✅ To proceed: clear_range(..., confirm=True)\n"
            result += "💡 Safer option: Clear specific columns instead of entire sheet"
            return result

        # Clear range
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()

        logger.info(
            "Range cleared: %s / %s (%s cells)",
            spreadsheet_id,
            range_name,
            filled_cells,
        )
        return f"✅ Cleared range {range_name} ({filled_cells:,} cells removed)."

    except Exception as e:
        logger.error("Error clearing range %s: %s", range_name, str(e))
        return f"❌ Error clearing range: {str(e)}"


def sheet_create_filter_view_handler(
    config: Config,
    logger: logging.Logger,
    spreadsheet_id: str,
    sheet_id: int,
    title: str,
    start_row: int = 0,
    end_row: Optional[int] = None,
    start_col: int = 0,
    end_col: Optional[int] = None,
) -> str:
    """Create a filter view for a sheet with a specified grid range."""
    try:
        creds = get_creds(config)
        service = build("sheets", "v4", credentials=creds)

        # If end_row/end_col not provided, use sheet properties
        if end_row is None or end_col is None:
            meta = service.spreadsheets().get(
                spreadsheetId=spreadsheet_id, fields="sheets.properties"
            ).execute()
            for s in meta.get("sheets", []):
                props = s.get("properties", {})
                if props.get("sheetId") == sheet_id:
                    grid = props.get("gridProperties", {})
                    if end_row is None:
                        end_row = grid.get("rowCount", 1000)
                    if end_col is None:
                        end_col = grid.get("columnCount", 26)
                    break

        range_obj = {
            "sheetId": sheet_id,
            "startRowIndex": start_row,
            "endRowIndex": end_row,
            "startColumnIndex": start_col,
            "endColumnIndex": end_col,
        }

        requests = [
            {
                "addFilterView": {
                    "filter": {"title": title, "range": range_obj}
                }
            }
        ]

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": requests}
        ).execute()

        logger.info(
            "Filter view created: %s sheet=%s title=%s",
            spreadsheet_id,
            sheet_id,
            title,
        )
        return f"✅ Filter view created: {title}"
    except Exception as e:
        logger.error("Error creating filter view: %s", str(e))
        return f"❌ Error creating filter view: {str(e)}"


def sheet_export_csv_handler(
    config: Config, logger: logging.Logger, spreadsheet_id: str, range_name: str, max_rows: int = 5000
) -> str:
    """Export range to CSV (values only)."""
    try:
        creds = get_creds(config)
        service = build("sheets", "v4", credentials=creds)

        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()
        values = result.get("values", [])

        if not values:
            return "No data found."

        # Apply row limit to keep output manageable
        values = values[:max_rows]

        def escape_csv(value: str) -> str:
            value = "" if value is None else str(value)
            if any(c in value for c in [",", '"', "\n"]):
                return '"' + value.replace('"', '""') + '"'
            return value

        csv_lines = []
        for row in values:
            csv_lines.append(",".join(escape_csv(v) for v in row))

        logger.info("CSV export: %s rows=%s", range_name, len(values))
        return "CSV Export:\n" + "\n".join(csv_lines)
    except Exception as e:
        logger.error("Error exporting CSV: %s", str(e))
        return f"❌ Error exporting CSV: {str(e)}"


def sheet_find_replace_handler(
    config: Config,
    logger: logging.Logger,
    spreadsheet_id: str,
    range_name: str,
    find_text: str,
    replace_text: str,
    dry_run: bool = True,
    match_case: bool = False,
) -> str:
    """Find/replace in a range with dry-run preview."""
    try:
        if not find_text:
            return "❌ find_text is required."

        creds = get_creds(config)
        service = build("sheets", "v4", credentials=creds)

        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()
        values = result.get("values", [])

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
                    new_value = (
                        cell_str.replace(find_text, replace_text)
                        if match_case
                        else _replace_ci(cell_str, find_text, replace_text)
                    )
                    new_row[c] = new_value
                    matches.append((r + 1, c + 1, cell_str, new_value))
            updated.append(new_row if row_changed else row)

        # Dry-run preview for safe inspection
        if dry_run:
            preview = matches[:20]
            output = f"🔍 DRY RUN: Found {len(matches)} matches\n"
            if preview:
                output += "Preview (row, col, before → after):\n"
                for r, c, before, after in preview:
                    output += f"- ({r}, {c}) {before} → {after}\n"
            output += "To apply changes, call again with dry_run=False"
            logger.info("Find/replace dry-run: %s matches=%s", range_name, len(matches))
            return output

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={"values": updated},
        ).execute()

        logger.info("Find/replace applied: %s matches=%s", range_name, len(matches))
        return f"✅ Replaced {len(matches)} occurrence(s)."
    except Exception as e:
        logger.error("Error in find/replace: %s", str(e))
        return f"❌ Error in find/replace: {str(e)}"


def _replace_ci(text: str, find_text: str, replace_text: str) -> str:
    """Case-insensitive replace preserving original casing where possible."""
    pattern = re.compile(re.escape(find_text), re.IGNORECASE)
    return pattern.sub(replace_text, text)


def sheet_create_named_range_handler(
    config: Config,
    logger: logging.Logger,
    spreadsheet_id: str,
    name: str,
    sheet_id: int,
    start_row: int,
    end_row: int,
    start_col: int,
    end_col: int,
) -> str:
    """Create a named range in a spreadsheet using grid indexes."""
    try:
        creds = get_creds(config)
        service = build("sheets", "v4", credentials=creds)

        requests = [
            {
                "addNamedRange": {
                    "namedRange": {
                        "name": name,
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": start_row,
                            "endRowIndex": end_row,
                            "startColumnIndex": start_col,
                            "endColumnIndex": end_col,
                        },
                    }
                }
            }
        ]

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": requests}
        ).execute()

        logger.info("Named range created: %s sheet=%s", name, sheet_id)
        return f"✅ Named range created: {name}"
    except Exception as e:
        logger.error("Error creating named range: %s", str(e))
        return f"❌ Error creating named range: {str(e)}"


def get_spreadsheet_meta_handler(
    config: Config, logger: logging.Logger, spreadsheet_id: str
) -> str:
    try:
        creds = get_creds(config)
        service = build("sheets", "v4", credentials=creds)

        sheet_metadata = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        properties = sheet_metadata.get("properties", {})
        sheets = sheet_metadata.get("sheets", [])

        output = (
            f"Spreadsheet: {properties.get('title')} (ID: {spreadsheet_id})\n"
            "Sheets:\n"
        )
        for sheet in sheets:
            props = sheet.get("properties", {})
            output += f"- {props.get('title')} (ID: {props.get('sheetId')})\n"

        return output
    except Exception as e:
        return f"Error getting metadata: {str(e)}"
