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

## Responsibility notice
You are responsible for understanding the risks and the consequences of
operations performed by this server. Use it at your own discretion and
follow your organization's security policies.
