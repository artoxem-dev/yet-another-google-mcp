# Настройка OAuth

Это руководство описывает настройку OAuth для MCP Google Tools server. Сервер использует **Installed Application** flow: вы один раз авторизуетесь в браузере, а токен сохраняется локально.

---

## Требования

- Python 3.8+
- Установленные зависимости: `pip install -r requirements.txt`
- При использовании YAML-конфига: `pip install pyyaml`

---

## Шаг 1: Откройте Google Cloud Console

1. Перейдите на [Google Cloud Console](https://console.cloud.google.com/)
2. Войдите в свой аккаунт Google

---

## Шаг 2: Создайте или выберите проект

1. В верхней панели нажмите на селектор проекта (рядом с «Google Cloud»)
2. Нажмите **New Project** (Создать проект) или выберите существующий
3. Введите название проекта (например, `mcp-google-tools`) и нажмите **Create**
4. Дождитесь создания проекта и выберите его

---

## Шаг 3: Настройте экран согласия OAuth

Настройка экрана согласия **обязательна** перед созданием OAuth-учётных данных.

1. В боковом меню: **APIs & Services** → **OAuth consent screen**
2. Выберите **External** (для работы с любым аккаунтом Google) и нажмите **Create**
3. Заполните обязательные поля:
   - **App name**: например, `MCP Google Tools`
   - **User support email**: ваш email
   - **Developer contact email**: ваш email
4. Нажмите **Save and Continue**
5. На странице **Scopes**: нажмите **Add or Remove Scopes** и добавьте нужные scope (или пропустите — сервер запросит их при авторизации)
6. Нажмите **Save and Continue**
7. На странице **Test users**:
   - Если приложение в режиме **Testing**, добавьте свой аккаунт Google в список тестовых пользователей
   - Можно добавить до 100 тестовых пользователей
8. Нажмите **Save and Continue**, затем **Back to Dashboard**

---

## Шаг 4: Включите необходимые API

1. Перейдите в **APIs & Services** → **Library**
2. Найдите и включите каждый API, который планируете использовать:

   | API                      | Назначение           |
   |--------------------------|----------------------|
   | Google Drive API         | Операции с Drive     |
   | Google Sheets API        | Таблицы              |
   | Google Docs API          | Документы            |
   | Gmail API                | Почта                |
   | Google Calendar API      | События календаря    |
   | Google Apps Script API   | Проекты Apps Script  |

3. Для каждого API: откройте его и нажмите **Enable**

---

## Шаг 5: Создайте OAuth Client ID

1. Перейдите в **APIs & Services** → **Credentials**
2. Нажмите **+ Create Credentials** → **OAuth client ID**
3. Если потребуется, сначала настройте экран согласия (см. Шаг 3)
4. В **Application type** выберите **Desktop app**
5. Введите **Name** (например, `MCP Google Tools Desktop`)
6. Нажмите **Create**
7. Появится диалог с **Client ID** и **Client Secret**
8. Нажмите **Download JSON**, чтобы сохранить файл учётных данных

---

## Шаг 6: Сохраните файл учётных данных

1. При необходимости переименуйте скачанный файл (например, в `oauth.keys.json`)
2. Поместите его в безопасное место, например:
   - Windows: `C:\Users\<username>\.google\oauth.keys.json`
   - macOS/Linux: `~/.google/oauth.keys.json`
3. Убедитесь, что путь совпадает с вашей конфигурацией (см. Шаг 7)

---

## Шаг 7: Настройте пути

Выберите один из вариантов:

### Вариант A: Через `config.yaml`

1. Скопируйте `config.example.yaml` в `config.yaml`
2. Укажите `client_secrets_file` полным путём к JSON-файлу:

   ```yaml
   client_secrets_file: "C:\\Users\\your_user\\.google\\oauth.keys.json"
   ```

3. Укажите `token_file` (куда сохранится OAuth-токен):

   ```yaml
   token_file: "C:\\Users\\your_user\\.google\\token.json"
   ```

4. Используйте переменную окружения `MCP_CONFIG_FILE`, указывающую на конфиг (например, в настройках MCP IDE)

### Вариант B: Через переменные окружения

Задайте их перед запуском сервера:

- `GOOGLE_CLIENT_SECRETS_FILE` — путь к скачанному JSON
- `GOOGLE_TOKEN_FILE` — путь для токена (по умолчанию `~/.google/token.json`)
- `MCP_CONFIG_FILE` — путь к `config.yaml` (если используете)

Пример (Windows PowerShell):

```powershell
$env:GOOGLE_CLIENT_SECRETS_FILE = "D:\path\to\oauth.keys.json"
```

Пример (macOS/Linux):

```bash
export GOOGLE_CLIENT_SECRETS_FILE="$HOME/.google/oauth.keys.json"
```

---

## Шаг 8: Первый запуск — авторизация в браузере

1. Запустите MCP-сервер (например, `python server.py` или через IDE)
2. При первом запуске **автоматически откроется окно браузера**
3. Войдите в свой аккаунт Google (если ещё не вошли)
4. Просмотрите запрашиваемые разрешения и нажмите **Allow** (Разрешить)
5. Может появиться «Приложение не проверено» — нажмите **Advanced** → **Go to ... (unsafe)**, если доверяете приложению (это ваше собственное)
6. После авторизации токен сохраняется в `token_file`
7. Закройте вкладку браузера — сервер продолжит работу

---

## Решение проблем

### «FileNotFoundError: Client secrets file not found»

- Проверьте, что `client_secrets_file` (или `GOOGLE_CLIENT_SECRETS_FILE`) указывает на правильный путь
- Используйте абсолютные пути; избегайте `~`, если shell его не раскрывает
- На Windows в YAML используйте двойные обратные слэши: `"C:\\Users\\..."`

### «The app isn't verified» / «Приложение не проверено»

- Нормально для приложений в режиме Testing
- Нажмите **Advanced** → **Go to [название приложения] (unsafe)** для продолжения
- Либо опубликуйте приложение (для продакшена потребуется верификация)

### Браузер не открывается / «Please visit this URL to authorize»

- Сервер выводит URL — откройте его вручную в браузере
- При работе без дисплея (SSH) выполните первую авторизацию на машине с браузером, затем скопируйте `token.json` на целевую машину

### «Access blocked: This app's request is invalid»

- Убедитесь, что экран согласия OAuth настроен (Шаг 3)
- Добавьте свой аккаунт в тестовые пользователи, если приложение в режиме Testing
- Проверьте, что используется правильный redirect URI (для Desktop app — `localhost`)

### Токен истёк / «Invalid credentials»

- Удалите `token.json` и запустите сервер снова для повторной авторизации
- Убедитесь, что выдали все необходимые scope

### Нужно изменить разрешения (scopes)

1. Отредактируйте `scopes` в `config.yaml` (см. `docs/SECURITY.md`)
2. Удалите `token.json`
3. Запустите сервер снова, чтобы получить новый токен с обновлёнными scopes

---

## Безопасность

- **Никогда не коммитьте** `oauth.keys.json` или `token.json` в репозиторий (они в `.gitignore`)
- Файл токена даёт полный доступ к выданным разрешениям — храните его как пароль
- Для продакшена рекомендуется ограничить scopes до read-only (см. `docs/SECURITY.md`)
