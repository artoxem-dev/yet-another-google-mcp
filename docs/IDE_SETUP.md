# IDE Setup (MCP Provider File)

This guide shows how to connect the server via the MCP provider config file in
popular IDEs. Use absolute paths to avoid working directory issues.

Before you start:
- Make sure the server works locally (`python server.py`).
- Configure `.env` and `config.yaml` as described in `README.md`.

Use this common configuration template (replace placeholders with your values):
 - Replace `<PROJECT_PATH>` with the absolute path to your local clone.
 - Set `MCP_AUTH_TOKEN` to your own token value.
 - Set `MCP_CONFIG_FILE` to the absolute path of your `config.yaml`.

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
Config file locations:
- Project: `.cursor/mcp.json`
- Global: `C:\\Users\\<YOU>\\.cursor\\mcp.json`

Format:
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

Format:
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
