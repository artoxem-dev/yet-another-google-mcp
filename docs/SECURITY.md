# Security and safeguards

The server includes safeguards to reduce accidental destructive actions.

## Confirmations (confirm)
- `delete_email`, `gmail_archive`, `calendar_create_meeting`,
  `drive_revoke_public` require `confirm=true`.
- `doc_fill_template` requires confirmation to avoid mass replacements.

## Dry-run
- `batch_delete_emails` defaults to dry-run.
- `sheet_find_replace` defaults to `dry_run=true`.
- `clear_range` automatically requires confirmation for large ranges.

## Public access
- `share_file` blocks `type=anyone` unless `allow_public=true`.

## MCP_AUTH_TOKEN
All calls require the server to run with `MCP_AUTH_TOKEN` set in the environment.
This is a basic protection against unauthorized use for STDIO-based servers.

## Understanding OAuth Scopes

OAuth scopes define what the server can access in your Google account. You can customize these in `config.yaml` under the `scopes:` section.

### Default Scopes (Full Access)
```yaml
scopes:
  - "https://www.googleapis.com/auth/spreadsheets"           # Read/write sheets
  - "https://www.googleapis.com/auth/drive"                   # Full Drive access
  - "https://www.googleapis.com/auth/documents"               # Read/write docs
  - "https://www.googleapis.com/auth/gmail.modify"            # Read/send/delete emails
  - "https://www.googleapis.com/auth/calendar"                # Manage calendar
  - "https://www.googleapis.com/auth/script.projects"         # Apps Script access
```

### Read-Only Configuration (Safer for Exploration)
```yaml
scopes:
  - "https://www.googleapis.com/auth/spreadsheets.readonly"
  - "https://www.googleapis.com/auth/drive.readonly"
  - "https://www.googleapis.com/auth/documents.readonly"
  - "https://www.googleapis.com/auth/gmail.readonly"
  - "https://www.googleapis.com/auth/calendar.readonly"
```

### Minimal Configuration (Sheets Only)
```yaml
scopes:
  - "https://www.googleapis.com/auth/spreadsheets"
```

### Custom Scenarios

**Scenario 1: Email assistant (read + draft)**
```yaml
scopes:
  - "https://www.googleapis.com/auth/gmail.readonly"
  - "https://www.googleapis.com/auth/gmail.compose"  # Draft only, no send
```

**Scenario 2: Document automation (Sheets + Docs)**
```yaml
scopes:
  - "https://www.googleapis.com/auth/spreadsheets"
  - "https://www.googleapis.com/auth/documents"
```

**Scenario 3: File organization (Drive only)**
```yaml
scopes:
  - "https://www.googleapis.com/auth/drive.file"  # Only files created by this app
```

### Changing Scopes
1. Edit `scopes:` in `config.yaml`
2. Delete your `token.json` file
3. Restart the server — a new OAuth prompt will appear with updated permissions

## Best Practices

### For Testing
- Create a separate Google account
- Use default scopes to test all features
- Keep test data separate from personal/work data

### For Production
- Use minimal scopes for your use case
- Review the scope list above and remove unused APIs
- Test with read-only scopes first, then add write permissions as needed

### For Work/Organization Accounts
- Check your organization's IT policies before connecting
- Consider using a dedicated service account
- Keep logs of operations for audit purposes
- Review the [Google Workspace Admin scope documentation](https://developers.google.com/identity/protocols/oauth2/scopes)

## AI Agent Access

**Important:** Your AI agent (MCP client) will have access to all data permitted by the OAuth scopes you grant. The `MCP_AUTH_TOKEN` prevents unauthorized access from other processes, but does not restrict the AI agent itself.

If you're concerned about accidental actions:
- Start with read-only scopes
- Use the built-in confirmations (`confirm=True`, `dry_run=False`)
- Test with a separate Google account first
- Monitor the server logs (`log_file` in config)

## Responsibility notice
You are responsible for understanding the risks and the consequences of
operations performed by this server. Use it at your own discretion and
follow your organization's security policies.

For questions about specific scopes, see [Google's OAuth 2.0 Scopes documentation](https://developers.google.com/identity/protocols/oauth2/scopes).
