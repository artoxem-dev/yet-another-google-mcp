# Настройка OAuth

1) Откройте Google Cloud Console: https://console.cloud.google.com/
2) Создайте проект или выберите существующий.
3) Включите нужные API:
   - Google Drive API
   - Google Sheets API
   - Google Docs API
   - Gmail API
   - Google Calendar API
   - Google Apps Script API
4) Создайте OAuth Client ID (Desktop app).
5) Скачайте JSON и сохраните в путь, указанный в конфиге:
   - `client_secrets_file` в `config.yaml`
   - или переменная окружения `GOOGLE_CLIENT_SECRETS_FILE`
6) При первом запуске откроется окно авторизации.
   Полученный токен будет сохранен в `token_file`.

Если используете YAML-конфиг, убедитесь, что PyYAML установлен:
`pip install pyyaml`
