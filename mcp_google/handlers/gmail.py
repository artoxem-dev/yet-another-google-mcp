import base64
from email.mime.text import MIMEText
from typing import List, Optional

from googleapiclient.discovery import build

from ..auth import get_creds
from ..config import Config
from ..security import validate_email


def _create_message(to: str, subject: str, message_text: str) -> dict:
    message = MIMEText(message_text)
    message["to"] = to
    message["from"] = "me"
    message["subject"] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return {"raw": raw_message}


def send_email_handler(
    config: Config,
    logger,
    to: str,
    subject: str,
    body_text: str,
    draft_mode: bool = True,
) -> str:
    """Send email with draft mode by default for safety."""
    try:
        if not validate_email(to):
            return f"❌ Invalid email format: {to}"

        creds = get_creds(config)
        service = build("gmail", "v1", credentials=creds)
        message = _create_message(to, subject, body_text)

        # Safe by default: create draft unless explicitly disabled
        if draft_mode:
            draft = {"message": message}
            created_draft = (
                service.users().drafts().create(userId="me", body=draft).execute()
            )
            draft_id = created_draft["id"]

            logger.info("Email draft created: %s to %s", draft_id, to)
            return (
                f"📝 EMAIL DRAFT CREATED (ID: {draft_id})\n\n"
                f"To: {to}\n"
                f"Subject: {subject}\n"
                f"Body: {body_text[:100]}{'...' if len(body_text) > 100 else ''}\n\n"
                "⚠️ Email saved as DRAFT, not sent yet.\n\n"
                "To send: send_email(..., draft_mode=False)\n"
                f"Or send draft: send_draft(draft_id='{draft_id}')"
            )

        sent_message = (
            service.users().messages().send(userId="me", body=message).execute()
        )
        logger.info("Email sent: %s to %s", sent_message["id"], to)
        return f"✅ Email sent. Message Id: {sent_message['id']}"

    except Exception as e:
        logger.error("Error sending email to %s: %s", to, str(e))
        return f"❌ Error sending email: {str(e)}"


def send_draft_handler(config: Config, logger, draft_id: str) -> str:
    """Send an existing draft."""
    try:
        creds = get_creds(config)
        service = build("gmail", "v1", credentials=creds)

        sent_message = (
            service.users()
            .drafts()
            .send(userId="me", body={"id": draft_id})
            .execute()
        )

        logger.info("Draft sent: %s", draft_id)
        return f"✅ Draft sent successfully. Message Id: {sent_message['id']}"

    except Exception as e:
        logger.error("Error sending draft %s: %s", draft_id, str(e))
        return f"❌ Error sending draft: {str(e)}"


def get_gmail_profile_handler(config: Config, logger) -> str:
    """Get the authenticated Gmail address (profile)."""
    try:
        creds = get_creds(config)
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        email_address = profile.get("emailAddress", "Unknown")
        logger.info("Gmail profile accessed: %s", email_address)
        return f"✅ Authenticated Gmail address: {email_address}"
    except Exception as e:
        logger.error("Error getting Gmail profile: %s", str(e))
        return f"❌ Error getting Gmail profile: {str(e)}"


def create_draft_handler(
    config: Config, logger, to: str, subject: str, body_text: str
) -> str:
    try:
        creds = get_creds(config)
        service = build("gmail", "v1", credentials=creds)

        message = _create_message(to, subject, body_text)
        draft = {"message": message}
        created_draft = (
            service.users().drafts().create(userId="me", body=draft).execute()
        )

        return f"Draft created. Draft Id: {created_draft['id']}"
    except Exception as e:
        return f"Error creating draft: {str(e)}"


def list_emails_handler(
    config: Config, logger, max_results: int = 10, query: Optional[str] = None
) -> str:
    try:
        creds = get_creds(config)
        service = build("gmail", "v1", credentials=creds)

        q = query if query else ""
        results = (
            service.users()
            .messages()
            .list(userId="me", maxResults=max_results, q=q)
            .execute()
        )
        messages = results.get("messages", [])

        if not messages:
            return "No messages found."

        output = "Messages:\n"
        for msg in messages:
            txt = (
                service.users()
                .messages()
                .get(userId="me", id=msg["id"], format="minimal")
                .execute()
            )
            snippet = txt.get("snippet", "")
            output += f"- ID: {msg['id']} | Snippet: {snippet}\n"

        return output
    except Exception as e:
        return f"Error listing emails: {str(e)}"


def read_email_handler(config: Config, logger, message_id: str) -> str:
    try:
        creds = get_creds(config)
        service = build("gmail", "v1", credentials=creds)

        message = (
            service.users().messages().get(userId="me", id=message_id).execute()
        )

        payload = message.get("payload", {})
        headers = payload.get("headers", [])

        subject = ""
        sender = ""
        for header in headers:
            if header["name"] == "Subject":
                subject = header["value"]
            if header["name"] == "From":
                sender = header["value"]

        snippet = message.get("snippet", "")

        return f"From: {sender}\nSubject: {subject}\nSnippet: {snippet}\n"
    except Exception as e:
        return f"Error reading email: {str(e)}"


def delete_email_handler(
    config: Config, logger, message_id: str, confirm: bool = False
) -> str:
    """Delete email with confirmation requirement."""
    try:
        creds = get_creds(config)
        service = build("gmail", "v1", credentials=creds)

        # Provide a preview before destructive action
        try:
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format="minimal")
                .execute()
            )
            snippet = msg.get("snippet", "No preview available")[:100]
        except Exception:
            snippet = "Unable to load preview"

        if not confirm:
            logger.warning("Delete email attempted without confirm: %s", message_id)
            return (
                "⚠️ CONFIRMATION REQUIRED\n\n"
                f"This will permanently delete email {message_id}.\n\n"
                f"Email preview:\n{snippet}...\n\n"
                "⚠️ To proceed, call this tool again with confirm=True"
            )

        service.users().messages().delete(userId="me", id=message_id).execute()
        logger.info("Email deleted: %s", message_id)
        return f"✅ Email {message_id} deleted successfully."

    except Exception as e:
        logger.error("Error deleting email %s: %s", message_id, str(e))
        return f"❌ Error deleting email: {str(e)}"


def batch_delete_emails_handler(
    config: Config, logger, message_ids: List[str], dry_run: bool = True
) -> str:
    """Batch delete emails with dry-run mode."""
    try:
        creds = get_creds(config)
        service = build("gmail", "v1", credentials=creds)

        if dry_run:
            preview = "🔍 DRY RUN MODE - No emails will be deleted\n\n"
            preview += f"Would delete {len(message_ids)} email(s):\n\n"

            previews_to_show = min(10, len(message_ids))
            for msg_id in message_ids[:previews_to_show]:
                try:
                    msg = (
                        service.users()
                        .messages()
                        .get(userId="me", id=msg_id, format="minimal")
                        .execute()
                    )
                    snippet = msg.get("snippet", "No preview")[:80]
                    preview += f"  • {msg_id}: {snippet}...\n"
                except Exception:
                    preview += f"  • {msg_id}: (unable to load preview)\n"

            if len(message_ids) > previews_to_show:
                preview += f"\n... and {len(message_ids) - previews_to_show} more\n"

            preview += "\n⚠️ To actually delete these emails, call with dry_run=False"
            logger.info("Batch delete dry-run: %s emails", len(message_ids))
            return preview

        body = {"ids": message_ids}
        service.users().messages().batchDelete(userId="me", body=body).execute()
        logger.info("Batch deleted %s emails", len(message_ids))
        return f"✅ Successfully deleted {len(message_ids)} email(s)."

    except Exception as e:
        logger.error("Error batch deleting emails: %s", str(e))
        return f"❌ Error batch deleting emails: {str(e)}"


def gmail_search_and_summarize_handler(
    config: Config, logger, query: str, max_results: int = 50
) -> str:
    """Search Gmail and return a brief summary."""
    try:
        creds = get_creds(config)
        service = build("gmail", "v1", credentials=creds)

        if not query:
            return "❌ Query is required."

        results = (
            service.users()
            .messages()
            .list(userId="me", maxResults=min(max_results, 100), q=query)
            .execute()
        )
        messages = results.get("messages", [])

        if not messages:
            return "No messages found."

        summary_lines = []
        for msg in messages[: min(len(messages), 20)]:
            full = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=msg["id"],
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                )
                .execute()
            )
            headers = {
                h["name"]: h["value"]
                for h in full.get("payload", {}).get("headers", [])
            }
            summary_lines.append(
                f"- {headers.get('Date','')} | {headers.get('From','')} | "
                f"{headers.get('Subject','')}"
            )

        logger.info("Gmail search: query='%s' results=%s", query, len(messages))
        output = f"Found {len(messages)} message(s) for query: {query}\n"
        output += "Top results:\n" + "\n".join(summary_lines)
        return output
    except Exception as e:
        logger.error("Error searching Gmail: %s", str(e))
        return f"❌ Error searching Gmail: {str(e)}"


def gmail_archive_handler(
    config: Config, logger, message_id: str, confirm: bool = False
) -> str:
    """Archive a Gmail message (remove INBOX label)."""
    try:
        if not confirm:
            return (
                "⚠️ CONFIRMATION REQUIRED\n\n"
                f"This will archive message {message_id} (remove from INBOX).\n"
                "To proceed, call again with confirm=True."
            )

        creds = get_creds(config)
        service = build("gmail", "v1", credentials=creds)

        service.users().messages().modify(
            userId="me", id=message_id, body={"removeLabelIds": ["INBOX"]}
        ).execute()

        logger.info("Gmail archived: %s", message_id)
        return f"✅ Message archived: {message_id}"
    except Exception as e:
        logger.error("Error archiving message: %s", str(e))
        return f"❌ Error archiving message: {str(e)}"


def _get_or_create_label_id(service, label_name: str, create_if_missing: bool = True):
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    for lbl in labels:
        if lbl.get("name") == label_name:
            return lbl.get("id")
    if not create_if_missing:
        return None
    created = (
        service.users()
        .labels()
        .create(
            userId="me",
            body={
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        )
        .execute()
    )
    return created.get("id")


def gmail_label_apply_handler(
    config: Config,
    logger,
    message_ids: List[str],
    label_name: str,
    dry_run: bool = True,
    create_if_missing: bool = True,
) -> str:
    """Apply a label to messages with dry-run preview."""
    try:
        if not message_ids:
            return "❌ message_ids is required."
        if not label_name:
            return "❌ label_name is required."

        creds = get_creds(config)
        service = build("gmail", "v1", credentials=creds)
        label_id = _get_or_create_label_id(service, label_name, create_if_missing)
        if not label_id:
            return f"❌ Label not found: {label_name}"

        if dry_run:
            preview_ids = message_ids[:10]
            logger.info(
                "Gmail label dry-run: %s count=%s", label_name, len(message_ids)
            )
            return (
                f"🔍 DRY RUN: Would apply label '{label_name}' to "
                f"{len(message_ids)} message(s).\n"
                f"Sample IDs: {', '.join(preview_ids)}\n"
                "To apply, call again with dry_run=False."
            )

        for mid in message_ids:
            service.users().messages().modify(
                userId="me", id=mid, body={"addLabelIds": [label_id]}
            ).execute()

        logger.info("Gmail label applied: %s count=%s", label_name, len(message_ids))
        return f"✅ Label '{label_name}' applied to {len(message_ids)} message(s)."
    except Exception as e:
        logger.error("Error applying label: %s", str(e))
        return f"❌ Error applying label: {str(e)}"
