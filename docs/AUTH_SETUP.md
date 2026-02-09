# OAuth Setup

1) Open Google Cloud Console: https://console.cloud.google.com/
2) Create a new project or select an existing one.
3) Enable required APIs:
   - Google Drive API
   - Google Sheets API
   - Google Docs API
   - Gmail API
   - Google Calendar API
   - Google Apps Script API
4) Create an OAuth Client ID (Desktop app).
5) Download the JSON and save it to the path from config:
   - `client_secrets_file` in `config.yaml`
   - or `GOOGLE_CLIENT_SECRETS_FILE` environment variable
6) On first run, an authorization window will open.
   The token will be saved to `token_file`.

If you use YAML config, install PyYAML:
`pip install pyyaml`
