# IDE Setup (MCP Provider File)

This guide shows how to connect the server via the MCP provider config file in
popular IDEs. Use absolute paths to avoid working directory issues.

Before you start:
- Make sure the server works locally (`python server.py`).
- Configure `config.yaml` as described in `README.md`.
- For STDIO servers, do not write to stdout (the server already logs to stderr).

## Choosing how to run the server

The IDE launches the server as a subprocess. Use one of two approaches:

**Option A — `uv run` (recommended):** No need to pre-install dependencies. [uv](https://docs.astral.sh/uv/) installs them on the fly. Install uv: `pip install uv` or `winget install astral-sh.uv`.

```json
{
  "command": "uv",
  "args": [
    "run",
    "--with", "google-api-python-client",
    "--with", "PyYAML",
    "--with", "google-auth",
    "--with", "google-auth-oauthlib",
    "--with", "mcp",
    "<PROJECT_PATH>\\\\server.py"
  ],
  "env": { "MCP_AUTH_TOKEN": "your_token_here", "MCP_CONFIG_FILE": "<PROJECT_PATH>\\\\config.yaml" }
}
```

**Option B — `python`:** Requires dependencies installed (`pip install -r requirements.txt`). The IDE must use the same Python interpreter (e.g. project venv). If you get `ModuleNotFoundError: No module named 'yaml'`, the IDE is using a different Python — switch to Option A or point the config to your venv’s `python.exe`.

Use this common configuration template (replace placeholders with your values):
 - Replace `<PROJECT_PATH>` with the absolute path to your local clone.
 - Set `MCP_AUTH_TOKEN` to your own token value.
 - Set `MCP_CONFIG_FILE` to the absolute path of your `config.yaml`.
 - If you already set environment variables in your OS, you can omit the `env` block.

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

## Smoke check
After connecting the server, call `get_gmail_profile()` to verify OAuth works.
