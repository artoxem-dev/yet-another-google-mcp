import logging
from typing import Optional

from googleapiclient.discovery import build

from ..auth import get_creds
from ..config import Config
from ..security import validate_email


def find_files_handler(config: Config, logger: logging.Logger, query: str) -> str:
    try:
        creds = get_creds(config)
        service = build("drive", "v3", credentials=creds)

        if "contains" not in query and "=" not in query:
            q = f"name contains '{query}' and trashed = false"
        else:
            q = query

        results = service.files().list(
            q=q, pageSize=10, fields="nextPageToken, files(id, name, mimeType)"
        ).execute()

        items = results.get("files", [])

        if not items:
            return "No files found."

        output = "Found files:\n"
        for item in items:
            output += (
                f"- {item['name']} (ID: {item['id']}) [{item['mimeType']}]\n"
            )

        return output
    except Exception as e:
        return f"Error searching files: {str(e)}"


def create_folder_handler(
    config: Config, logger: logging.Logger, name: str, parent_id: Optional[str] = None
) -> str:
    try:
        creds = get_creds(config)
        service = build("drive", "v3", credentials=creds)

        file_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            file_metadata["parents"] = [parent_id]

        file = service.files().create(body=file_metadata, fields="id").execute()
        return f"Folder created: {name} (ID: {file.get('id')})"
    except Exception as e:
        return f"Error creating folder: {str(e)}"


def move_file_handler(config: Config, logger: logging.Logger, file_id: str, folder_id: str) -> str:
    try:
        creds = get_creds(config)
        service = build("drive", "v3", credentials=creds)

        # Retrieve the existing parents to remove
        file = service.files().get(fileId=file_id, fields="parents").execute()
        previous_parents = ",".join(file.get("parents"))

        # Move the file to the new folder
        service.files().update(
            fileId=file_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields="id, parents",
        ).execute()
        return f"File moved to folder ID {folder_id}."
    except Exception as e:
        return f"Error moving file: {str(e)}"


def share_file_handler(
    config: Config,
    logger: logging.Logger,
    file_id: str,
    role: str,
    type: str = "user",
    email_address: Optional[str] = None,
    allow_public: bool = False,
) -> str:
    """Share file with public access protection."""
    try:
        creds = get_creds(config)
        service = build("drive", "v3", credentials=creds)

        # Block public sharing without explicit confirmation
        if type == "anyone" and not allow_public:
            try:
                file_info = service.files().get(
                    fileId=file_id, fields="name,size,mimeType,owners"
                ).execute()
                file_name = file_info.get("name", "Unknown")
                file_size = int(file_info.get("size", 0)) / (1024 * 1024)
            except Exception:
                file_name = "Unknown"
                file_size = 0

            logger.warning("Public sharing blocked for file: %s", file_id)
            return (
                "⚠️ PUBLIC ACCESS BLOCKED\n\n"
                "You are trying to make this file PUBLIC:\n"
                f"  📄 {file_name}\n"
                f"  📊 Size: {file_size:.2f} MB\n"
                "  🔗 Will be accessible to: ANYONE with the link\n\n"
                "⚠️ SECURITY WARNING:\n"
                "  • File may be indexed by search engines\n"
                "  • Anyone can view, download and share it\n"
                "  • You cannot track who accessed it\n\n"
                "To proceed, you must explicitly set allow_public=True\n\n"
                "✅ Safer alternative: Share with specific users using type='user'"
            )

        if type in ["user", "group"] and email_address:
            if not validate_email(email_address):
                return f"❌ Invalid email format: {email_address}"

        permission = {"type": type, "role": role}
        if email_address:
            permission["emailAddress"] = email_address

        service.permissions().create(fileId=file_id, body=permission).execute()

        logger.info(
            "File shared: %s (%s=%s, role=%s)",
            file_id,
            type,
            email_address or "anyone",
            role,
        )

        result = "✅ File shared successfully\n\n"
        result += f"📄 File ID: {file_id}\n"
        result += f"🌐 Access: {type}\n"
        result += f"👤 Role: {role}\n"

        if type == "anyone":
            result += "\n⚠️ This file is now PUBLIC"

        return result

    except Exception as e:
        logger.error("Error sharing file %s: %s", file_id, str(e))
        return f"❌ Error sharing file: {str(e)}"


def drive_search_advanced_handler(
    config: Config, logger: logging.Logger, query: str, limit: int = 50
) -> str:
    """Advanced Drive search with query and limit."""
    try:
        creds = get_creds(config)
        service = build("drive", "v3", credentials=creds)

        if not query:
            return "❌ Query is required."

        results = service.files().list(
            q=query,
            pageSize=min(max(limit, 1), 100),
            fields="files(id, name, mimeType, owners, modifiedTime)",
        ).execute()

        items = results.get("files", [])
        if not items:
            return "No files found."

        output = "Found files:\n"
        for item in items:
            owners = item.get("owners", [])
            owner = owners[0].get("emailAddress") if owners else "Unknown"
            output += (
                f"- {item.get('name')} (ID: {item.get('id')}) "
                f"[{item.get('mimeType')}] owner={owner} "
                f"modified={item.get('modifiedTime')}\n"
            )

        logger.info("Drive search: query='%s' results=%s", query, len(items))
        return output
    except Exception as e:
        logger.error("Error searching files (advanced): %s", str(e))
        return f"Error searching files: {str(e)}"


def drive_list_permissions_handler(config: Config, logger: logging.Logger, file_id: str) -> str:
    """List permissions for a Drive file."""
    try:
        creds = get_creds(config)
        service = build("drive", "v3", credentials=creds)

        perms = service.permissions().list(
            fileId=file_id,
            fields="permissions(id,type,role,emailAddress,domain,allowFileDiscovery)",
        ).execute()

        items = perms.get("permissions", [])
        if not items:
            return "No permissions found."

        output = f"Permissions for file {file_id}:\n"
        for p in items:
            target = p.get("emailAddress") or p.get("domain") or "anyone"
            output += (
                f"- id={p.get('id')} type={p.get('type')} "
                f"role={p.get('role')} target={target}\n"
            )

        logger.info("Drive permissions listed: %s count=%s", file_id, len(items))
        return output
    except Exception as e:
        logger.error("Error listing permissions for %s: %s", file_id, str(e))
        return f"Error listing permissions: {str(e)}"


def drive_revoke_public_handler(
    config: Config, logger: logging.Logger, file_id: str, confirm: bool = False
) -> str:
    """Revoke public access (type=anyone) for a Drive file."""
    try:
        creds = get_creds(config)
        service = build("drive", "v3", credentials=creds)

        perms = service.permissions().list(
            fileId=file_id, fields="permissions(id,type,role,allowFileDiscovery)"
        ).execute()
        items = perms.get("permissions", [])
        public_perms = [p for p in items if p.get("type") == "anyone"]

        if not public_perms:
            return "No public permissions found."

        if not confirm:
            return (
                "⚠️ CONFIRMATION REQUIRED\n\n"
                f"Public access permissions found: {len(public_perms)}\n"
                "To revoke, call again with confirm=True."
            )

        for p in public_perms:
            service.permissions().delete(
                fileId=file_id, permissionId=p.get("id")
            ).execute()

        logger.info(
            "Public access revoked: %s count=%s", file_id, len(public_perms)
        )
        return f"✅ Public access revoked for file {file_id}."
    except Exception as e:
        logger.error("Error revoking public access for %s: %s", file_id, str(e))
        return f"Error revoking public access: {str(e)}"


def drive_copy_file_handler(
    config: Config,
    logger: logging.Logger,
    file_id: str,
    name: Optional[str] = None,
    parent_id: Optional[str] = None,
) -> str:
    """Copy a Drive file to a new file."""
    try:
        creds = get_creds(config)
        service = build("drive", "v3", credentials=creds)

        body = {}
        if name:
            body["name"] = name
        if parent_id:
            body["parents"] = [parent_id]

        copied = service.files().copy(
            fileId=file_id, body=body, fields="id,name"
        ).execute()
        logger.info("File copied: %s -> %s", file_id, copied.get("id"))
        return f"✅ File copied: {copied.get('name')} (ID: {copied.get('id')})"
    except Exception as e:
        logger.error("Error copying file %s: %s", file_id, str(e))
        return f"Error copying file: {str(e)}"
