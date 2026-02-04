# MCP Google Tools Server

MCP сервер для работы с Google Drive, Sheets, Docs, Gmail, Calendar и Apps Script.
Проект разделен на модули, чтобы было проще читать, расширять и публиковать.

## Возможности
- Drive: поиск, перемещение, копирование, права доступа.
- Sheets: чтение/запись, очистка диапазонов, find/replace, экспорт CSV.
- Docs: чтение, создание, заполнение шаблонов, экспорт PDF.
- Gmail: черновики, отправка, поиск, удаление с подтверждением.
- Calendar: события, свободные слоты, встречи с подтверждением.
- Apps Script: чтение, подготовка обновлений с backup и rollback.

## Быстрый старт
1) Установите зависимости:
   - `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib`
   - MCP пакет: установите ваш MCP runtime/SDK (зависит от среды запуска)

2) Настройте OAuth:
   - Создайте OAuth Client ID в Google Cloud Console.
   - Скачайте файл `oauth.keys.json` и положите его в удобный путь.
   - Подробно: см. `docs/AUTH_SETUP.md`.

3) Настройте конфигурацию:
   - Скопируйте `.env.example` → `.env`.
   - Скопируйте `config.example.yaml` → `config.yaml`.
   - Укажите пути и `MCP_AUTH_TOKEN`.

4) Запустите сервер:
   - `python server.py`

## Конфигурация
Поддерживается комбинированный подход:
- ENV: `MCP_AUTH_TOKEN`, `GOOGLE_CLIENT_SECRETS_FILE`, `GOOGLE_TOKEN_FILE`,
  `GOOGLE_BACKUP_DIR`, `GOOGLE_LOG_FILE`, `MCP_CONFIG_FILE`.
- Config-файл: `client_secrets_file`, `token_file`, `backup_dir`, `log_file`, `scopes`.

Если указан `MCP_CONFIG_FILE`, его значения будут использованы как дефолты,
а ENV переменные их переопределят.

## Безопасность
Некоторые операции требуют подтверждения или выполняются в dry-run режиме:
- Удаление писем, архивирование, публичный доступ к файлам.
- Очистка больших диапазонов в Sheets.
Подробнее: `docs/SECURITY.md`.

## Документация
- `docs/AUTH_SETUP.md` — настройка OAuth.
- `docs/TOOLS_REFERENCE.md` — параметры всех MCP tools.
- `docs/SECURITY.md` — защитные механизмы.
