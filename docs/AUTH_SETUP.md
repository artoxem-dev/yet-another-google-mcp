# OAuth Setup

This guide walks you through setting up OAuth for the MCP Google Tools server. The server uses the **Installed Application** flow: you authorize in a browser once, and the token is saved locally.

---

## Prerequisites

- Python 3.8+
- Dependencies installed: `pip install -r requirements.txt`
- If using YAML config: `pip install pyyaml`

---

## Step 1: Open Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account

---

## Step 2: Create or Select a Project

1. In the top bar, click the project selector (next to "Google Cloud")
2. Click **New Project** to create one, or select an existing project
3. Enter a project name (e.g. `mcp-google-tools`) and click **Create**
4. Wait for the project to be created, then select it

---

## Step 3: Configure the OAuth Consent Screen

Configuring the consent screen is **required** before you can create OAuth credentials.

1. In the left sidebar, go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** (to use with any Google account) and click **Create**
3. Fill in the required fields:
   - **App name**: e.g. `MCP Google Tools`
   - **User support email**: your email
   - **Developer contact email**: your email
4. Click **Save and Continue**
5. On the **Scopes** page: click **Add or Remove Scopes**, then add the scopes you need (or skip for now — the server will request them during auth)
6. Click **Save and Continue**
7. On the **Test users** page:
   - If your app is in **Testing** mode, add your Google account(s) as test users
   - You can add up to 100 test users
8. Click **Save and Continue**, then **Back to Dashboard**

---

## Step 4: Enable Required APIs

1. Go to **APIs & Services** → **Library**
2. Search for and enable each API you plan to use:

   | API Name           | Used for                 |
   |--------------------|--------------------------|
   | Google Drive API   | Drive operations         |
   | Google Sheets API  | Spreadsheets             |
   | Google Docs API    | Documents                |
   | Gmail API          | Email                    |
   | Google Calendar API| Calendar events          |
   | Google Apps Script API | Apps Script projects |

3. For each API: open it and click **Enable**

---

## Step 5: Create OAuth Client ID

1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. If prompted, configure the consent screen first (see Step 3)
4. For **Application type**, select **Desktop app**
5. Enter a **Name** (e.g. `MCP Google Tools Desktop`)
6. Click **Create**
7. A dialog will show your **Client ID** and **Client Secret**
8. Click **Download JSON** to save the credentials file

---

## Step 6: Save the Credentials File

1. Rename the downloaded file if needed (e.g. to `oauth.keys.json`)
2. Place it in a secure location, for example:
   - Windows: `C:\Users\<username>\.google\oauth.keys.json`
   - macOS/Linux: `~/.google/oauth.keys.json`
3. Ensure the path matches your configuration (see Step 7)

---

## Step 7: Configure Paths

Choose one of these options:

### Option A: Using `config.yaml`

1. Copy `config.example.yaml` to `config.yaml`
2. Set `client_secrets_file` to the full path of your JSON file:

   ```yaml
   client_secrets_file: "C:\\Users\\your_user\\.google\\oauth.keys.json"
   ```

3. Set `token_file` (where the OAuth token will be saved):

   ```yaml
   token_file: "C:\\Users\\your_user\\.google\\token.json"
   ```

4. Use `MCP_CONFIG_FILE` env var pointing to your config (e.g. in IDE MCP config)

### Option B: Using Environment Variables

Set these before starting the server:

- `GOOGLE_CLIENT_SECRETS_FILE` — path to the downloaded JSON
- `GOOGLE_TOKEN_FILE` — path for the token (optional; defaults to `~/.google/token.json`)
- `MCP_CONFIG_FILE` — path to `config.yaml` (if you use it)

Example (Windows PowerShell):

```powershell
$env:GOOGLE_CLIENT_SECRETS_FILE = "D:\path\to\oauth.keys.json"
```

Example (macOS/Linux):

```bash
export GOOGLE_CLIENT_SECRETS_FILE="$HOME/.google/oauth.keys.json"
```

---

## Step 8: First Run — Authorize in Browser

1. Start the MCP server (e.g. `python server.py` or via your IDE)
2. On first run, a **browser window will open** automatically
3. Sign in with your Google account (if not already)
4. Review the requested permissions and click **Allow**
5. You may see "The app isn't verified" — click **Advanced** → **Go to ... (unsafe)** if you trust the app (it's your own)
6. After authorization, the token is saved to `token_file`
7. Close the browser tab — the server continues running

---

## Troubleshooting

### "FileNotFoundError: Client secrets file not found"

- Check that `client_secrets_file` (or `GOOGLE_CLIENT_SECRETS_FILE`) points to the correct path
- Use absolute paths; avoid `~` unless your shell expands it
- On Windows, use double backslashes in YAML: `"C:\\Users\\..."

### "The app isn't verified" / "This app hasn't been verified"

- Normal for apps in Testing mode
- Click **Advanced** → **Go to [app name] (unsafe)** to proceed
- Or publish your app (requires verification for production use)

### Browser doesn't open / "Please visit this URL to authorize"

- The server prints a URL — open it manually in your browser
- If running headless (SSH, no display), use a machine with a browser for the first authorization, then copy `token.json` to the headless machine

### "Access blocked: This app's request is invalid"

- Ensure the OAuth consent screen is configured (Step 3)
- Add your account as a test user if the app is in Testing mode
- Check that the correct redirect URI is used (Desktop app uses `localhost`)

### Token expired / "Invalid credentials"

- Delete `token.json` and run the server again to re-authorize
- Ensure you granted all required scopes

### Need to change scopes

1. Edit `scopes` in `config.yaml` (see `docs/SECURITY.md` for options)
2. Delete `token.json`
3. Run the server again to get a new token with updated scopes

---

## Security Notes

- **Never commit** `oauth.keys.json` or `token.json` to version control (they are in `.gitignore`)
- The token file gives full access to the scopes you authorized — protect it like a password
- For production, consider limiting scopes to read-only (see `docs/SECURITY.md`)
