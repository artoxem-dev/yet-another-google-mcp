import os
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from .config import Config


def get_creds(config: Config) -> Credentials:
    """Get OAuth credentials, refreshing or running auth flow if needed."""
    creds: Optional[Credentials] = None

    if os.path.exists(config.token_file):
        try:
            creds = Credentials.from_authorized_user_file(
                config.token_file, config.scopes
            )
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not os.path.exists(config.client_secrets_file):
                raise FileNotFoundError(
                    f"Client secrets file not found at {config.client_secrets_file}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                config.client_secrets_file, config.scopes
            )
            creds = flow.run_local_server(port=0)

        token_dir = os.path.dirname(config.token_file)
        if token_dir:
            os.makedirs(token_dir, exist_ok=True)
        with open(config.token_file, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return creds
