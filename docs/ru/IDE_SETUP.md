# Настройка IDE (файл MCP-провайдера)

Эта инструкция показывает, как подключить сервер через файл конфигурации
MCP‑провайдера в популярных IDE. Используйте абсолютные пути, чтобы не было
проблем с рабочей директорией.

Перед началом:
- Убедитесь, что сервер запускается локально (`python server.py`).
- Настройте `.env` и `config.yaml`, как описано в `README.md`.

Общий шаблон (замените плейсхолдеры на свои значения):
- Замените `<PROJECT_PATH>` на абсолютный путь к вашему локальному клону.
- Укажите `MCP_AUTH_TOKEN` — ваш собственный токен.
- Укажите `MCP_CONFIG_FILE` — абсолютный путь к вашему `config.yaml`.
- Если переменные среды уже заданы в ОС, блок `env` можно опустить.

```
{
  "command": "python",
  "args": ["<PROJECT_PATH>\\\\server.py"],
  "env": {
    "MCP_AUTH_TOKEN": "your_token_here",
    "MCP_CONFIG_FILE": "<PROJECT_PATH>\\\\config.yaml"
  }
}
```

## Cursor
Файлы конфигурации:
- Проектный: `.cursor/mcp.json`
- Глобальный: `C:\\Users\\<YOU>\\.cursor\\mcp.json`

Формат:
```
{
  "mcpServers": {
    "google-tools": {
      "command": "python",
      "args": ["<PROJECT_PATH>\\\\server.py"],
      "env": {
        "MCP_AUTH_TOKEN": "your_token_here",
        "MCP_CONFIG_FILE": "<PROJECT_PATH>\\\\config.yaml"
      }
    }
  }
}
```

## Windsurf
Файлы конфигурации (по ОС):
- Windows: `%APPDATA%\\Codeium\\Windsurf\\mcp_config.json`
- macOS: `~/.codeium/windsurf/mcp_config.json`
- Linux: `~/.config/Codeium/Windsurf/mcp_config.json`

Формат:
```
{
  "mcpServers": {
    "google-tools": {
      "command": "python",
      "args": ["<PROJECT_PATH>\\\\server.py"],
      "env": {
        "MCP_AUTH_TOKEN": "your_token_here",
        "MCP_CONFIG_FILE": "<PROJECT_PATH>\\\\config.yaml"
      }
    }
  }
}
```

## VS Code (Copilot MCP)
Требования:
- VS Code 1.102+ и включённый Copilot.

Файлы конфигурации:
- Проектный: `.vscode/mcp.json`
- Пользовательский: команда `MCP: Open User Configuration`

Формат (в VS Code ключ `servers`, а не `mcpServers`):
```
{
  "servers": {
    "google-tools": {
      "type": "stdio",
      "command": "python",
      "args": ["<PROJECT_PATH>\\\\server.py"],
      "env": {
        "MCP_AUTH_TOKEN": "your_token_here",
        "MCP_CONFIG_FILE": "<PROJECT_PATH>\\\\config.yaml"
      }
    }
  }
}
```

## Другие IDE
Если IDE поддерживает MCP stdio‑серверы, найдите конфиг MCP‑провайдера и
используйте те же `command/args/env`. Название ключа может отличаться
(например, `mcpServers` или `servers`).
