# Безопасность и ответственность

В сервере есть встроенные защиты, чтобы снизить риск случайных разрушительных действий.

## Подтверждения (confirm)
- `delete_email`, `gmail_archive`, `calendar_create_meeting`,
  `drive_revoke_public` требуют `confirm=true`.
- `doc_fill_template` требует подтверждения, чтобы избежать массовой замены.

## Dry-run
- `batch_delete_emails` по умолчанию выполняется в dry-run.
- `sheet_find_replace` по умолчанию `dry_run=true`.
- `clear_range` автоматически требует подтверждения для больших диапазонов.

## Публичный доступ
- `share_file` запрещает `type=anyone` без `allow_public=true`.

## MCP_AUTH_TOKEN
Все вызовы требуют, чтобы `MCP_AUTH_TOKEN` был сконфигурирован (переменная
окружения или `mcp_auth_token` в `config.yaml`). Это **проверка конфигурации
на стороне сервера**, которая гарантирует, что оператор осознанно включил
сервер. Она **не выполняет** аутентификацию клиента на уровне каждого запроса.

Для STDIO-серверов транспорт по своей природе локальный (IDE запускает процесс
напрямую), поэтому сетевая точка доступа для защиты отсутствует. Токен просто
предотвращает случайные запуски без осознанного шага настройки.

## Понимание OAuth Scopes

OAuth scopes определяют, к каким данным в вашем Google аккаунте получает доступ сервер. Вы можете настроить их в `config.yaml` в секции `scopes:`.

### Scopes по умолчанию (полный доступ)
```yaml
scopes:
  - "https://www.googleapis.com/auth/spreadsheets"           # Чтение/запись таблиц
  - "https://www.googleapis.com/auth/drive"                   # Полный доступ к Drive
  - "https://www.googleapis.com/auth/documents"               # Чтение/запись документов
  - "https://www.googleapis.com/auth/gmail.modify"            # Чтение/отправка/удаление писем (включает чтение)
  - "https://www.googleapis.com/auth/calendar"                # Управление календарём
  - "https://www.googleapis.com/auth/script.projects"         # Доступ к Apps Script
  - "https://www.googleapis.com/auth/script.deployments"      # Деплои Apps Script
```

> Примечание: `gmail.modify` уже включает доступ на чтение, поэтому отдельный
> scope `gmail.readonly` не нужен.

### Конфигурация только для чтения (безопаснее для тестирования)
```yaml
scopes:
  - "https://www.googleapis.com/auth/spreadsheets.readonly"
  - "https://www.googleapis.com/auth/drive.readonly"
  - "https://www.googleapis.com/auth/documents.readonly"
  - "https://www.googleapis.com/auth/gmail.readonly"
  - "https://www.googleapis.com/auth/calendar.readonly"
```

### Минимальная конфигурация (только таблицы)
```yaml
scopes:
  - "https://www.googleapis.com/auth/spreadsheets"
```

### Примеры для конкретных задач

**Сценарий 1: Email-ассистент (чтение + черновики)**
```yaml
scopes:
  - "https://www.googleapis.com/auth/gmail.readonly"
  - "https://www.googleapis.com/auth/gmail.compose"  # Только черновики, без отправки
```

**Сценарий 2: Автоматизация документов (Sheets + Docs)**
```yaml
scopes:
  - "https://www.googleapis.com/auth/spreadsheets"
  - "https://www.googleapis.com/auth/documents"
```

**Сценарий 3: Организация файлов (только Drive)**
```yaml
scopes:
  - "https://www.googleapis.com/auth/drive.file"  # Только файлы, созданные этим приложением
```

### Изменение scopes
1. Отредактируйте `scopes:` в `config.yaml`
2. Удалите файл `token.json`
3. Перезапустите сервер — появится новое окно OAuth с обновлёнными разрешениями

## Рекомендации по настройке

### Для тестирования
- Создайте отдельный Google аккаунт для тестов
- Используйте scopes по умолчанию, чтобы протестировать все функции
- Храните тестовые данные отдельно от личных/рабочих

### Для постоянного использования
- Используйте минимальные scopes для вашей задачи
- Изучите список scopes выше и уберите ненужные API
- Сначала протестируйте с read-only scopes, затем добавьте права на запись

### Для рабочих/корпоративных аккаунтов
- Проверьте политики безопасности вашей организации перед подключением
- Рассмотрите использование служебного аккаунта с ограниченными правами
- Ведите логи операций для аудита
- Изучите [документацию Google Workspace Admin по scopes](https://developers.google.com/identity/protocols/oauth2/scopes)

## Доступ AI агента

**Важно:** Ваш AI агент (MCP клиент) получит доступ ко всем данным, разрешённым OAuth scopes. `MCP_AUTH_TOKEN` — это проверка конфигурации, а не механизм клиентской аутентификации; он не ограничивает самого AI агента.

Если вы беспокоитесь о случайных действиях:
- Начните с read-only scopes
- Используйте встроенные подтверждения (`confirm=True`, `dry_run=False`)
- Протестируйте на отдельном Google аккаунте
- Следите за логами сервера (`log_file` в конфиге)

## Уведомление об ответственности
Пользователь несёт ответственность за понимание рисков и последствий
операций, выполняемых этим сервером. Используйте его на свой риск и
в соответствии с политиками безопасности вашей организации.

Для вопросов о конкретных scopes см. [документацию Google OAuth 2.0 Scopes](https://developers.google.com/identity/protocols/oauth2/scopes).
