# IDE Setup (MCP Provider File)

This guide shows how to connect the server via the MCP provider config file in
popular IDEs. Use absolute paths to avoid working directory issues.

Before you start:
- Install dependencies: `pip install -r requirements.txt`
- Make sure the server works locally (`python server.py`)
- Configure `config.yaml` as described in `README.md`
- For STDIO servers, do not write to stdout (the server already logs to stderr)

The IDE launches the server as a subprocess. Use `python` and ensure the IDE
uses the same Python interpreter where you installed the dependencies (e.g. project venv).

Replace placeholders:
- `<PROJECT_PATH>` — absolute path to your local clone
- `your_token_here` — your `MCP_AUTH_TOKEN` value
- If environment variables are already set in your OS, you can omit the `env` block

## Cursor
Config file locations:
- Project: `.cursor/mcp.json`
- Global: `C:\\Users\\<YOU>\\.cursor\\mcp.json`

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
Config file locations (by OS):
- Windows: `%APPDATA%\\Codeium\\Windsurf\\mcp_config.json`
- macOS: `~/.codeium/windsurf/mcp_config.json`
- Linux: `~/.config/Codeium/Windsurf/mcp_config.json`

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
Requirements:
- VS Code 1.102+ and Copilot enabled.

Config file locations:
- Workspace: `.vscode/mcp.json`
- User: use command `MCP: Open User Configuration`

Format (VS Code uses `servers`, not `mcpServers`):
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

## Other IDEs
If your IDE supports MCP stdio servers, look for an MCP provider configuration
file and add the same command/args/env as above. The key name may differ
(for example, `mcpServers` or `servers`).

## Smoke check
After connecting the server, call `get_gmail_profile()` to verify OAuth works.
