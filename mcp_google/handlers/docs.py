import logging
from typing import Dict, Union

from googleapiclient.discovery import build

from ..auth import get_creds
from ..config import Config
from ..operations import BinaryResult


def read_doc_handler(config: Config, logger: logging.Logger, document_id: str) -> str:
    try:
        creds = get_creds(config)
        service = build("docs", "v1", credentials=creds)

        document = service.documents().get(documentId=document_id).execute()
        content = document.get("body").get("content")

        text_content = ""
        for value in content:
            if "paragraph" in value:
                elements = value.get("paragraph").get("elements")
                for elem in elements:
                    text_content += elem.get("textRun", {}).get("content", "")

        return f"Document Content ({document.get('title')}):\n{text_content}"
    except Exception as e:
        return f"Error reading document: {str(e)}"


def create_doc_handler(config: Config, logger: logging.Logger, title: str) -> str:
    try:
        creds = get_creds(config)
        service = build("docs", "v1", credentials=creds)

        body = {"title": title}
        doc = service.documents().create(body=body).execute()

        return f"Created document: {doc.get('title')} (ID: {doc.get('documentId')})"
    except Exception as e:
        return f"Error creating document: {str(e)}"


def append_to_doc_handler(config: Config, logger: logging.Logger, document_id: str, text: str) -> str:
    try:
        creds = get_creds(config)
        service = build("docs", "v1", credentials=creds)

        requests = [
            {
                "insertText": {
                    "endOfSegmentLocation": {"segmentId": ""},
                    "text": text,
                }
            }
        ]

        service.documents().batchUpdate(
            documentId=document_id, body={"requests": requests}
        ).execute()

        return "Successfully appended text to document."
    except Exception as e:
        return f"Error appending to document: {str(e)}"


def doc_fill_template_handler(
    config: Config,
    logger: logging.Logger,
    document_id: str,
    replacements: Dict[str, str],
    confirm: bool = False,
) -> str:
    """Fill a Google Doc template by replacing placeholders."""
    try:
        if not replacements:
            return "❌ replacements map is required."

        # Two-step safety: confirm before writing
        if not confirm:
            keys = ", ".join(list(replacements.keys())[:20])
            return (
                "⚠️ CONFIRMATION REQUIRED\n\n"
                f"This will replace placeholders in document {document_id}.\n"
                f"Keys: {keys}\n"
                "To proceed, call again with confirm=True."
            )

        creds = get_creds(config)
        service = build("docs", "v1", credentials=creds)

        requests = []
        for key, value in replacements.items():
            requests.append(
                {
                    "replaceAllText": {
                        "containsText": {"text": key, "matchCase": True},
                        "replaceText": str(value),
                    }
                }
            )

        service.documents().batchUpdate(
            documentId=document_id, body={"requests": requests}
        ).execute()

        logger.info("Doc template filled: %s keys=%s", document_id, len(replacements))
        return f"✅ Document updated: {len(replacements)} placeholders replaced."
    except Exception as e:
        logger.error("Error filling template %s: %s", document_id, str(e))
        return f"❌ Error filling template: {str(e)}"


def doc_export_pdf_handler(
    config: Config, logger: logging.Logger, document_id: str
) -> Union[BinaryResult, str]:
    """Export a Google Doc to PDF and return it as binary content."""
    try:
        creds = get_creds(config)
        drive = build("drive", "v3", credentials=creds)

        data: bytes = drive.files().export(
            fileId=document_id, mimeType="application/pdf"
        ).execute()

        logger.info("Doc exported to PDF: %s bytes=%s", document_id, len(data))
        return BinaryResult(
            uri=f"gdocs://{document_id}/export.pdf",
            mime_type="application/pdf",
            data=data,
            description=f"PDF export of document {document_id} ({len(data):,} bytes)",
        )
    except Exception as e:
        logger.error("Error exporting PDF %s: %s", document_id, str(e))
        return f"❌ Error exporting PDF: {str(e)}"
