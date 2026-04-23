# DaVinci Resolve MCP Server

[![Version](https://img.shields.io/badge/version-1.3.8-blue.svg)](https://github.com/samuelgursky/davinci-resolve-mcp/releases)
[![DaVinci Resolve](https://img.shields.io/badge/DaVinci%20Resolve-18.5+-darkred.svg)](https://www.blackmagicdesign.com/products/davinciresolve)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/downloads/)
[![macOS](https://img.shields.io/badge/macOS-stable-brightgreen.svg)](https://www.apple.com/macos/)
[![Windows](https://img.shields.io/badge/Windows-stable-brightgreen.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server that exposes DaVinci Resolve's scripting API as **273 tools** and **38 resources** for AI assistants. Connect Cursor, Claude Desktop, or Claude Code to control DaVinci Resolve through natural language.

## Capabilities

| Module | Tools | Resources | Description |
|--------|-------|-----------|-------------|
| Navigation | 4 | 2 | Page switching, system info |
| Project | 49 | 12 | Lifecycle, settings, presets, cloud |
| Media | 42 | 10 | MediaPool: clips, metadata, markers, mattes |
| MediaStorage | 6 | 1 | Mounted volumes, file browsing |
| Timeline | 72 | 7 | Tracks, items, markers, stereo, cache |
| Color | 38 | 0 | Node graph, LUTs, gallery, color groups |
| Fairlight | 13 | 0 | Audio mixing, voice isolation |
| Fusion | 11 | 2 | Compositions, Text+, templates |
| Delivery | 14 | 4 | Render queue, formats, quick export |
| **Total** | **273** | **38** | **311 endpoints** |

The server also includes an **AI Director** subsystem with four editing personas (viral clips, highlights, tutorials, podcasts) powered by LLM integration. See [Agents.md](Agents.md) for details.

Full tool/resource reference: [CAPABILITIES.md](CAPABILITIES.md)

## Requirements

- **Python 3.10+** (tested on 3.10, 3.11)
- **DaVinci Resolve 18.5+** (Studio recommended)
- **macOS** or **Windows**
- DaVinci Resolve running in the background

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/samuelgursky/davinci-resolve-mcp.git
   cd davinci-resolve-mcp
   ```

2. Make sure DaVinci Resolve is running.

3. Run the install script:

   **macOS:**
   ```bash
   ./install.sh
   ```

   **Windows:**
   ```batch
   run-now.bat
   ```

   This will create a virtual environment, install dependencies, set up environment variables, and configure your AI client.

For manual installation or troubleshooting, see [INSTALL.md](INSTALL.md).

## Client Configuration

### Cursor

Create or edit `~/.cursor/mcp.json` (macOS) or `%APPDATA%\Cursor\mcp.json` (Windows):

```json
{
  "mcpServers": {
    "davinci-resolve": {
      "name": "DaVinci Resolve MCP",
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/davinci-resolve-mcp/src/main.py"]
    }
  }
}
```

Use absolute paths. On Windows, use `venv\\Scripts\\python.exe`.

### Claude Desktop

Use the templates in the [config/](config/) directory:
- macOS: `config/macos/claude-desktop-config.template.json`
- Windows: `config/windows/claude-desktop-config.template.json`

Replace `${PROJECT_ROOT}` with the actual project path.

### Claude Code

Claude Code connects via MCP protocol automatically. Configure with the same JSON format pointing to `src/main.py`.

## Server Variants

| Variant | Command | Modules | Use Case |
|---------|---------|---------|----------|
| `full` (default) | `python src/main.py` | All 9 modules (273 tools) | Full functionality |
| `edit` | `python src/main.py --variant edit` | Media + Timeline only | Edit page focus, faster startup |

Additional flags: `--debug` enables debug logging.

## Launch Scripts

| Script | Purpose |
|--------|---------|
| `scripts/mcp_resolve-cursor_start` | Launch for Cursor integration |
| `scripts/mcp_resolve-claude_start` | Launch for Claude Desktop |
| `scripts/mcp_resolve_launcher.sh` | Universal launcher with interactive menu |
| `scripts/check-resolve-ready.sh` / `.bat` | Pre-flight environment check |
| `scripts/run-now.sh` / `run-now.bat` | One-step setup and launch |

Universal launcher options:
```bash
./scripts/mcp_resolve_launcher.sh --start-cursor   # Start Cursor server
./scripts/mcp_resolve_launcher.sh --start-claude    # Start Claude server
./scripts/mcp_resolve_launcher.sh --start-both      # Start both
./scripts/mcp_resolve_launcher.sh --stop-all        # Stop all servers
./scripts/mcp_resolve_launcher.sh --status          # Show status
```

## Project Structure

```
davinci-resolve-mcp/
├── src/
│   ├── main.py                  # CLI entry point
│   ├── resolve_mcp_server.py    # Full server variant
│   ├── server_edit.py           # Edit-page server variant
│   ├── server_instance.py       # Shared FastMCP instance
│   ├── context.py               # Global Resolve connection state
│   ├── tools/                   # MCP tool modules (9 modules, 273 tools)
│   ├── api/                     # DaVinci Resolve API wrappers (15 modules)
│   └── utils/                   # Platform, connection, error handling (8 modules)
├── config/                      # Client configuration templates (macOS/Windows)
├── scripts/                     # Launch, diagnostic, and automation scripts
├── tests/                       # Unit and integration tests (pytest)
├── examples/                    # Usage examples (markers, media, timeline)
└── docs/                        # Extended documentation
```

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, layers, data flow, design decisions |
| [CAPABILITIES.md](CAPABILITIES.md) | Full tool and resource reference (273 + 38) |
| [INSTALL.md](INSTALL.md) | Detailed installation and troubleshooting guide |
| [Agents.md](Agents.md) | AI Director personas and workflows |
| [CONTEXT.md](CONTEXT.md) | Architectural quick-reference for AI assistants |
| [TECH_STACK.md](TECH_STACK.md) | Technology stack details |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | API reference |
| [docs/FEATURES.md](docs/FEATURES.md) | Feature status and testing matrix |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Version history |

## Development

### Adding a New Tool

1. Implement API function in `src/api/<domain>_operations.py`
2. Create tool wrapper with `@mcp.tool()` in `src/tools/<domain>.py`
3. Import the tool module in `src/resolve_mcp_server.py` (if new module)
4. Add tests in `tests/unit/`

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture and conventions.

### Testing

```bash
# All tests
pytest tests/

# Unit tests only (no DaVinci required)
pytest tests/unit/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

CI runs on GitHub Actions with Python 3.10/3.11.

## Troubleshooting

### Connection Issues
- DaVinci Resolve must be running before starting the server
- Verify environment variables are set correctly (run `scripts/check-resolve-ready.sh` or `.bat`)
- Check logs in `scripts/cursor_resolve_server.log`

### Windows
- Use forward slashes (/) in JSON configuration files
- Python and paths must be configured in config files
- Default DaVinci Resolve installation path expected

### macOS
- Ensure scripts have execute permissions (`chmod +x`)
- Check Console.app for Python-related errors
- Verify environment variables are set

For detailed troubleshooting, see [INSTALL.md](INSTALL.md#troubleshooting).

## Platform Support

| Platform | Status |
|----------|--------|
| macOS | Stable |
| Windows | Stable |
| Linux | Not supported |

## License

MIT

## Author

Samuel Gursky (samgursky@gmail.com)
- GitHub: [github.com/samuelgursky](https://github.com/samuelgursky)

## Acknowledgments

- Blackmagic Design for DaVinci Resolve and its scripting API
- The MCP protocol team for enabling AI assistant integration
