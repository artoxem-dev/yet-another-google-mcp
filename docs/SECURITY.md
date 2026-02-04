# Безопасность и защитные механизмы

В сервере есть несколько встроенных защит, чтобы избежать случайных разрушительных действий.

## Подтверждения (confirm)
- `delete_email`, `gmail_archive`, `calendar_create_meeting`,
  `drive_revoke_public` требуют `confirm=true`.
- `doc_fill_template` требует подтверждения, чтобы избежать массовой замены.

## Dry-run
- `batch_delete_emails` по умолчанию выполняется в dry-run.
- `sheet_find_replace` по умолчанию `dry_run=true`.
- `clear_range` автоматически предлагает dry-run для больших диапазонов.

## Публичный доступ
- `share_file` запрещает `type=anyone` без `allow_public=true`.

## MCP_AUTH_TOKEN
Все вызовы требуют `auth_token` и совпадения с `MCP_AUTH_TOKEN`.
Это базовая защита от несанкционированных вызовов.
