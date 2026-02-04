# MCP Tools Reference

Ниже перечислены инструменты (tools), доступные в MCP сервере.

## Drive
- `find_files(query)`
  - Поиск по имени или по полноценному запросу Drive query.
- `create_folder(name, parent_id?)`
  - Создать папку; `parent_id` опционален.
- `move_file(file_id, folder_id)`
  - Переместить файл в папку.
- `share_file(file_id, role, type?, email_address?, allow_public?)`
  - `type`: `user|group|domain|anyone`, публичный доступ только с `allow_public=true`.
- `drive_search_advanced(query, limit?)`
  - Полный синтаксис Drive query.
- `drive_list_permissions(file_id)`
  - Список прав доступа.
- `drive_revoke_public(file_id, confirm?)`
  - Отозвать публичный доступ, требует `confirm=true`.
- `drive_copy_file(file_id, name?, parent_id?)`
  - Копировать файл.

## Sheets
- `read_sheet(spreadsheet_id, range_name)`
  - Чтение диапазона.
- `append_row(spreadsheet_id, range_name, values[])`
  - Добавить строку.
- `update_sheet(spreadsheet_id, range_name, values[][])`
  - Обновить диапазон массивом строк.
- `create_spreadsheet(title)`
  - Создать таблицу.
- `add_sheet(spreadsheet_id, title)`
  - Добавить новый лист (tab).
- `clear_range(spreadsheet_id, range_name, confirm?)`
  - Для больших диапазонов требуется `confirm=true`.
- `sheet_create_filter_view(spreadsheet_id, sheet_id, title, start_row?, end_row?, start_col?, end_col?)`
  - Создать фильтр-вью.
- `sheet_export_csv(spreadsheet_id, range_name, max_rows?)`
  - Экспорт диапазона в CSV.
- `sheet_find_replace(spreadsheet_id, range_name, find_text, replace_text, dry_run?, match_case?)`
  - По умолчанию `dry_run=true`.
- `sheet_create_named_range(spreadsheet_id, name, sheet_id, start_row, end_row, start_col, end_col)`
  - Именованный диапазон по индексам.
- `get_spreadsheet_meta(spreadsheet_id)`
  - Метаданные таблицы.

## Docs
- `read_doc(document_id)`
  - Прочитать текст документа.
- `create_doc(title)`
  - Создать документ.
- `append_to_doc(document_id, text)`
  - Добавить текст в конец.
- `doc_fill_template(document_id, replacements, confirm?)`
  - Заполнить шаблон, требует `confirm=true`.
- `doc_export_pdf(document_id)`
  - Экспорт PDF (base64).

## Gmail
- `send_email(to, subject, body_text, draft_mode?)`
  - По умолчанию создает черновик.
- `send_draft(draft_id)`
  - Отправить черновик.
- `get_gmail_profile()`
  - Получить адрес текущего аккаунта.
- `create_draft(to, subject, body_text)`
  - Создать черновик.
- `list_emails(max_results?, query?)`
  - Список писем.
- `read_email(message_id)`
  - Прочитать письмо (snippet).
- `delete_email(message_id, confirm?)`
  - Требует `confirm=true`.
- `batch_delete_emails(message_ids[], dry_run?)`
  - По умолчанию `dry_run=true`.
- `gmail_search_and_summarize(query, max_results?)`
  - Поиск и краткое резюме.
- `gmail_archive(message_id, confirm?)`
  - Требует `confirm=true`.
- `gmail_label_apply(message_ids[], label_name, dry_run?, create_if_missing?)`
  - По умолчанию `dry_run=true`.

## Calendar
- `list_events(calendar_id?, max_results?)`
  - Список ближайших событий.
- `create_event(summary, start_time, end_time, description?)`
  - Создать событие.
- `calendar_find_free_slots(calendar_id?, start_time, end_time, duration_minutes?, max_results?)`
  - Найти свободные слоты.
- `calendar_create_meeting(summary, start_time, end_time, attendees?, description?, location?, confirm?)`
  - Требует `confirm=true`.

## Apps Script
- `create_script_project(title, parent_id?)`
  - Создать проект Apps Script.
- `get_script_content(script_id)`
  - Получить контент.
- `prepare_script_update(script_id, files[])`
  - Подготовка обновления, возвращает `operation_id`.
- `execute_operation(operation_id)`
  - Выполнить подготовленную операцию.
- `cancel_operation(operation_id)`
  - Отменить подготовленную операцию.
- `restore_script_backup(backup_path)`
  - Откатить из backup.
