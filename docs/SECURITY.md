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
All tool calls require `MCP_AUTH_TOKEN` to be configured (environment variable or
`mcp_auth_token` in `config.yaml`). This is a **server-side configuration check**
that ensures the operator has consciously enabled the server before it becomes
operational. It does **not** perform per-request client authentication.

For STDIO-based MCP servers the transport is inherently local (the IDE launches the
server process directly), so there is no network endpoint to protect. The token
simply prevents accidental starts without a deliberate setup step.

## Understanding OAuth Scopes

OAuth scopes define what the server can access in your Google account. You can customize these in `config.yaml` under the `scopes:` section.

### Default Scopes (Full Access)
```yaml
scopes:
  - "https://www.googleapis.com/auth/spreadsheets"           # Read/write sheets
  - "https://www.googleapis.com/auth/drive"                   # Full Drive access
  - "https://www.googleapis.com/auth/documents"               # Read/write docs
  - "https://www.googleapis.com/auth/gmail.modify"            # Read/send/delete emails (includes read)
  - "https://www.googleapis.com/auth/calendar"                # Manage calendar
  - "https://www.googleapis.com/auth/script.projects"         # Apps Script access
  - "https://www.googleapis.com/auth/script.deployments"      # Apps Script deployments
```

> Note: `gmail.modify` already includes read access, so a separate `gmail.readonly`
> scope is not needed.

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

**Important:** Your AI agent (MCP client) will have access to all data permitted by the OAuth scopes you grant. The `MCP_AUTH_TOKEN` is a configuration check, not a client-facing authentication mechanism — it does not restrict the AI agent itself.

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
