from datetime import datetime
from typing import Dict, List, Optional

from googleapiclient.discovery import build

from ..auth import get_creds
from ..config import Config
from ..operations import (
    cleanup_expired_operations,
    create_backup,
    new_operation_id,
    pending_operations,
)


def create_script_project_handler(
    config: Config, logger, title: str, parent_id: Optional[str] = None
) -> str:
    try:
        creds = get_creds(config)
        service = build("script", "v1", credentials=creds)

        request = {"title": title}
        if parent_id:
            request["parentId"] = parent_id

        response = service.projects().create(body=request).execute()
        return (
            f"Script created: {response.get('title')} "
            f"(ID: {response.get('scriptId')})\n"
            f"URL: {response.get('scriptId')}"
        )
    except Exception as e:
        return f"Error creating script: {str(e)}"


def get_script_content_handler(config: Config, logger, script_id: str) -> str:
    try:
        creds = get_creds(config)
        service = build("script", "v1", credentials=creds)

        content = service.projects().getContent(scriptId=script_id).execute()
        files = content.get("files", [])

        output = f"Script Content ({script_id}):\n"
        for file in files:
            output += f"\n--- File: {file.get('name')} ({file.get('type')}) ---\n"
            output += file.get("source", "")

        return output
    except Exception as e:
        return f"Error reading script content: {str(e)}"


def prepare_script_update_handler(
    config: Config, logger, script_id: str, files: List[Dict[str, str]]
) -> str:
    """STEP 1: Prepare script update with backup."""
    try:
        cleanup_expired_operations()

        creds = get_creds(config)
        service = build("script", "v1", credentials=creds)

        # Get current content for backup
        current_content = service.projects().getContent(scriptId=script_id).execute()
        current_files = current_content.get("files", [])

        # Create operation ID
        op_id = new_operation_id()

        # Store pending operation
        pending_operations[op_id] = {
            "type": "script_update",
            "script_id": script_id,
            "backup": current_files,
            "new_files": files,
            "created_at": datetime.now().isoformat(),
        }

        # Analyze changes for a clear preview
        old_files = {f["name"]: f for f in current_files}
        new_files = {f["name"]: f for f in files}

        changes = []
        for name in new_files:
            if name not in old_files:
                changes.append(f"  + NEW: {name}")
            else:
                old_lines = old_files[name].get("source", "").count("\n")
                new_lines = new_files[name].get("source", "").count("\n")
                diff = new_lines - old_lines
                changes.append(f"  ~ MODIFIED: {name} ({diff:+d} lines)")

        for name in old_files:
            if name not in new_files:
                changes.append(f"  - DELETED: {name}")

        result = f"📋 Script Update Prepared (Operation ID: {op_id})\n\n"
        result += f"Script ID: {script_id}\n"
        result += f"Backup created: {len(current_files)} file(s)\n\n"
        result += "📊 Changes:\n" + "\n".join(changes) + "\n\n"
        result += "⏰ Operation expires in: 10 minutes\n\n"
        result += f"✅ To execute: execute_operation(operation_id='{op_id}')\n"
        result += f"❌ To cancel: cancel_operation(operation_id='{op_id}')"

        logger.info("Script update prepared: %s for %s", op_id, script_id)
        return result

    except Exception as e:
        logger.error("Error preparing script update: %s", str(e))
        return f"❌ Error preparing update: {str(e)}"


def execute_operation_handler(config: Config, logger, operation_id: str) -> str:
    """STEP 2: Execute a prepared operation."""
    try:
        cleanup_expired_operations()

        if operation_id not in pending_operations:
            return f"❌ Operation {operation_id} not found or expired"

        op = pending_operations[operation_id]

        if op["type"] == "script_update":
            creds = get_creds(config)
            service = build("script", "v1", credentials=creds)

            # Create backup file before applying changes
            backup_path = create_backup(
                op["backup"], "script", op["script_id"], config.backup_dir, logger
            )

            # Execute update
            request = {"files": op["new_files"]}
            service.projects().updateContent(
                scriptId=op["script_id"], body=request
            ).execute()

            # Remove from pending
            del pending_operations[operation_id]

            logger.info(
                "Script updated: %s (backup: %s)", op["script_id"], backup_path
            )

            return (
                "✅ Script updated successfully!\n\n"
                "📊 Results:\n"
                f"  • Files updated: {len(op['new_files'])}\n"
                f"  • Script ID: {op['script_id']}\n\n"
                "💾 Backup saved to:\n"
                f"   {backup_path}\n\n"
                "🔄 To rollback: restore_script_backup("
                f"backup_path='{backup_path}')"
            )

        return f"❌ Unknown operation type: {op['type']}"

    except Exception as e:
        logger.error("Error executing operation %s: %s", operation_id, str(e))
        return f"❌ Error executing operation: {str(e)}"


def cancel_operation_handler(config: Config, logger, operation_id: str) -> str:
    """Cancel a prepared operation."""
    cleanup_expired_operations()

    if operation_id in pending_operations:
        del pending_operations[operation_id]
        logger.info("Operation cancelled: %s", operation_id)
        return f"✅ Operation {operation_id} cancelled"

    return f"❌ Operation {operation_id} not found"


def restore_script_backup_handler(
    config: Config, logger, backup_path: str
) -> str:
    """Restore script from backup file."""
    try:
        import os
        import json

        if not os.path.exists(backup_path):
            return f"❌ Backup file not found: {backup_path}"

        with open(backup_path, "r", encoding="utf-8") as f:
            backup_data = json.load(f)

        # Extract script_id from filename: backup_script_SCRIPTID_TIMESTAMP.json
        filename = os.path.basename(backup_path)
        parts = filename.split("_")
        if len(parts) < 3:
            return "❌ Invalid backup filename format"

        script_id = parts[2]

        creds = get_creds(config)
        service = build("script", "v1", credentials=creds)

        request = {"files": backup_data}
        service.projects().updateContent(scriptId=script_id, body=request).execute()

        logger.info("Script restored from backup: %s <- %s", script_id, backup_path)
        return f"✅ Script {script_id} restored from backup successfully!"

    except Exception as e:
        logger.error("Error restoring backup: %s", str(e))
        return f"❌ Error restoring backup: {str(e)}"
