# DaVinci Resolve MCP Server

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/samuelgursky/davinci-resolve-mcp/releases)
[![API Coverage](https://img.shields.io/badge/API%20Coverage-100%25-brightgreen.svg)](docs/API_COVERAGE.md)
[![DaVinci Resolve](https://img.shields.io/badge/DaVinci%20Resolve-18.5+-darkred.svg)](https://www.blackmagicdesign.com/products/davinciresolve)
[![Python](https://img.shields.io/badge/python-3.6+-green.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> **🎉 100% API Coverage Achieved!** All 339 DaVinci Resolve API methods now available through MCP!

A comprehensive Model Context Protocol (MCP) server that provides complete programmatic control of DaVinci Resolve through AI assistants like Cursor and Claude Desktop. Control editing, color grading, media management, delivery, and AI-powered features through natural language.

---

## 🌟 What's New in v2.0

**Complete API Coverage**: We've achieved **100% coverage** of the official DaVinci Resolve API (339/339 methods)!

### Phase 6 Additions (71% → 100%):
- ✨ **98 new tools** across 10 comprehensive modules
- 🎨 **Advanced Color Grading**: Color versions, take selector, CDL, group-level grading
- 🤖 **AI-Powered Features**: Magic Mask, Smart Reframe, Stabilization, Auto-captions, Scene detection
- 🎬 **Professional Workflows**: Compound clips, Fusion compositions, proxy media, media relinking
- 📦 **Media Management**: Timeline import/export (AAF/EDL/XML/FCPXML), auto-sync audio
- 🖼️ **Gallery & Stills**: Complete PowerGrade and still album management
- ⚡ **Performance**: Cache control, optimized operations, batch processing

**[View Complete API Coverage Documentation →](docs/API_COVERAGE.md)**

---

## 📋 Table of Contents

- [Features](#-features)
- [Requirements](#-requirements)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Examples](#-usage-examples)
- [API Coverage](#-api-coverage)
- [Architecture](#-architecture)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)
- [License](#-license)

---

## ✨ Features

### Complete DaVinci Resolve Control

**Editing & Timeline** (100+ tools)
- Timeline creation, manipulation, and export
- Compound clips, Fusion clips, and nested timelines
- Clip operations: trim, ripple delete, link/unlink
- Timecode management and navigation
- Generator and title insertion (standard, Fusion, OFX)
- Marker and flag management

**Color Grading** (80+ tools)
- Color versions for A/B comparison
- Take selector operations
- CDL (Color Decision List) operations
- Color groups with pre/post-clip grading
- Node graph access and manipulation
- LUT management and export
- PowerGrade album management
- Gallery still operations

**AI & Machine Learning** (15+ tools)
- ✨ Magic Mask creation and regeneration
- ✨ Smart Reframe for social media
- ✨ Stabilization
- ✨ Auto-caption generation
- ✨ Scene cut detection
- ✨ Auto-sync audio (waveform analysis)
- ✨ Audio transcription

**Media Management** (60+ tools)
- Media Pool folder operations
- Timeline import (AAF, EDL, XML, FCPXML, DRT, ADL, OTIO)
- Proxy media linking/unlinking
- Media relinking for offline clips
- Clip and folder movement
- Metadata import/export
- Stereo 3D clip creation

**Delivery & Rendering** (40+ tools)
- Render preset management
- Burn-in preset operations
- Quick Export workflows
- Format and codec selection
- Custom render settings
- Job queue management

**Fusion Integration** (25+ tools)
- Fusion composition management
- Composition import/export
- Node graph operations
- Generator insertion

**Project & Database** (30+ tools)
- Project creation and management
- Database switching
- Cloud project support
- Archive and restore operations
- Preset management

### Two Modes of Operation

#### 1. **Search/Execute Mode** (Recommended for Cursor)
Perfect for AI assistants with tool limits (like Cursor's 40-tool limit):
- **4 core tools** provide access to all 339+ operations
- Search tools by name, category, or description
- Execute any tool dynamically
- Optimized for natural language interaction

#### 2. **Full Tool Mode** (For Claude Desktop)
Direct access to all individual tools:
- **339+ tools** exposed directly
- Better for auto-completion
- Ideal for clients without tool limits

---

## 📦 Requirements

- **Operating System**: macOS or Windows (Linux not currently supported)
- **DaVinci Resolve**: Version 18.5 or higher (Studio or Free)
- **Python**: 3.6 or higher
- **DaVinci Resolve**: Must be running for the MCP server to connect

**Recommended AI Clients:**
- [Cursor](https://cursor.sh/) - AI-powered code editor
- [Claude Desktop](https://claude.ai/download) - Anthropic's desktop app

---

## 🚀 Quick Start

### One-Step Installation (Recommended)

**macOS:**
```bash
git clone https://github.com/samuelgursky/davinci-resolve-mcp.git
cd davinci-resolve-mcp
./install.sh
```

**Windows:**
```batch
git clone https://github.com/samuelgursky/davinci-resolve-mcp.git
cd davinci-resolve-mcp
install.bat
```

The installer will:
1. ✅ Detect your DaVinci Resolve installation
2. ✅ Create a Python virtual environment
3. ✅ Install all dependencies (MCP SDK, FastMCP)
4. ✅ Set up environment variables
5. ✅ Configure Cursor/Claude integration
6. ✅ Verify the installation
7. ✅ Optionally start the server

### Quick Launch

After installation, use the quick start scripts:

**macOS:**
```bash
./run-now.sh
```

**Windows:**
```batch
run-now.bat
```

---

## 📥 Installation

### Prerequisites

1. **Install DaVinci Resolve**
   - Download from [Blackmagic Design](https://www.blackmagicdesign.com/products/davinciresolve)
   - Install in the default location

2. **Install Python 3.6+**
   - macOS: `brew install python3` or download from [python.org](https://python.org)
   - Windows: Download from [python.org](https://python.org)

3. **Install an AI Assistant** (optional but recommended)
   - [Cursor](https://cursor.sh/) - Recommended for developers
   - [Claude Desktop](https://claude.ai/download) - Recommended for general use

### Manual Installation

If you prefer manual setup or the automated installer doesn't work:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/samuelgursky/davinci-resolve-mcp.git
   cd davinci-resolve-mcp
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv

   # Activate (macOS/Linux)
   source venv/bin/activate

   # Activate (Windows)
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables:**

   **macOS:**
   ```bash
   export RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
   export RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
   export PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
   ```

   **Windows:**
   ```cmd
   set RESOLVE_SCRIPT_API=C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting
   set RESOLVE_SCRIPT_LIB=C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll
   set PYTHONPATH=%PYTHONPATH%;%RESOLVE_SCRIPT_API%\Modules
   ```

5. **Verify installation:**
   ```bash
   # macOS
   ./scripts/check-resolve-ready.sh

   # Windows
   scripts\check-resolve-ready.bat
   ```

---

## ⚙️ Configuration

### For Cursor

Create or edit `~/.cursor/mcp.json` (macOS) or `%APPDATA%\Cursor\mcp.json` (Windows):

```json
{
  "mcpServers": {
    "davinci-resolve": {
      "name": "DaVinci Resolve MCP",
      "command": "/path/to/davinci-resolve-mcp/venv/bin/python",
      "args": ["/path/to/davinci-resolve-mcp/src/main.py"],
      "env": {
        "RESOLVE_MCP_MODE": "search_execute"
      }
    }
  }
}
```

**Configuration Options:**
- `RESOLVE_MCP_MODE`:
  - `"search_execute"` (recommended) - Use 4-tool search/execute interface
  - `"full"` - Expose all 339+ tools directly

### For Claude Desktop

Create or edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "davinci-resolve": {
      "command": "/path/to/davinci-resolve-mcp/venv/bin/python",
      "args": ["/path/to/davinci-resolve-mcp/src/main.py"],
      "env": {
        "RESOLVE_MCP_MODE": "full"
      }
    }
  }
}
```

**See [config-templates/](config-templates/) for more examples.**

---

## 💡 Usage Examples

### Basic Operations

**Get DaVinci Resolve Information:**
```
What version of DaVinci Resolve is running?
```

**Project Management:**
```
List all projects in DaVinci Resolve
Create a new project called "Documentary Edit"
Open the project named "Commercial 2024"
```

**Timeline Operations:**
```
Create a new timeline called "Main Sequence" at 24fps
List all timelines in the current project
Switch to timeline "Main Sequence"
Add a marker at the current position with the note "Review this shot"
```

### Advanced Workflows

**Color Grading:**
```
Create a color version called "Hero Look" for the current clip
Apply a CDL with slope 1.2, offset 0.01, and saturation 1.1
Create a color group called "Day Exteriors"
Export a 33-point LUT from the current clip to /exports/hero_look.cube
```

**AI-Powered Features:**
```
Create a Magic Mask for the person in the current clip
Apply Smart Reframe to optimize for Instagram (9:16)
Stabilize the current clip
Generate auto-captions from the timeline audio
Detect scene cuts in the timeline
```

**Media Management:**
```
Import timeline from /imports/sequence.xml
Relink all offline clips to the folder /media/new_location/
Auto-sync audio for clips A001 through A010
Create a stereo 3D clip from left_eye.mov and right_eye.mov
Move clips to the B-Roll folder
```

**Editing:**
```
Create a compound clip from clips 1, 2, and 3 on video track 1
Delete clips 5 and 6 with ripple delete
Link clips 1, 2, and 3 on video track 1
Duplicate the current timeline as "Main Sequence - Backup"
```

**Fusion & VFX:**
```
Add a Fusion composition to the current clip
Import Fusion comp from /comps/vfx_shot.comp
Export the Fusion composition to /exports/my_comp.comp
Insert a Fusion generator called "3D Text" at the playhead
```

**Delivery:**
```
Export the timeline to AAF format at /exports/sequence.aaf
Set the render format to QuickTime and codec to ProRes 422 HQ
Add the current timeline to the render queue
Start rendering all jobs
```

### Batch Operations

**Process Multiple Clips:**
```
For all clips in the Media Pool folder "Interviews":
1. Apply the same grade from clip "A001"
2. Add a marker at 5 seconds with "Check audio levels"
3. Enable auto-sync audio
```

**Timeline Automation:**
```
Create 5 timelines named "Episode 1" through "Episode 5" at 24fps
For each timeline, import the corresponding XML from /imports/
```

---

## 📊 API Coverage

We provide **100% coverage** of the official DaVinci Resolve API (339/339 methods):

### Coverage by Object

| Object | Total Methods | Implemented | Coverage |
|--------|---------------|-------------|----------|
| **Resolve** | 21 | 21 | 100% ✅ |
| **ProjectManager** | 25 | 25 | 100% ✅ |
| **Project** | 38 | 38 | 100% ✅ |
| **MediaStorage** | 7 | 7 | 100% ✅ |
| **MediaPool** | 24 | 24 | 100% ✅ |
| **MediaPoolItem** | 23 | 23 | 100% ✅ |
| **Folder** | 7 | 7 | 100% ✅ |
| **Timeline** | 42 | 42 | 100% ✅ |
| **TimelineItem** | 55 | 55 | 100% ✅ |
| **Gallery** | 8 | 8 | 100% ✅ |
| **GalleryStillAlbum** | 6 | 6 | 100% ✅ |
| **Graph** | 11 | 11 | 100% ✅ |
| **ColorGroup** | 5 | 5 | 100% ✅ |
| **TOTAL** | **339** | **339** | **100%** ✅ |

### Tools by Category

- **Core & Project**: 30+ tools
- **Timeline & Editing**: 100+ tools
- **Color Grading**: 80+ tools
- **Media Management**: 60+ tools
- **Delivery & Rendering**: 40+ tools
- **Fusion Integration**: 25+ tools
- **Gallery & Stills**: 20+ tools
- **AI/ML Features**: 15+ tools
- **Advanced Operations**: 50+ tools

**[View Detailed API Coverage →](docs/API_COVERAGE.md)**

---

## 🏗️ Architecture

### Project Structure

```
davinci-resolve-mcp/
├── src/
│   ├── main.py                    # Entry point
│   ├── resolve_mcp_server.py      # Core MCP server
│   ├── proxy.py                   # Tool proxy layer
│   └── tools/                     # Tool modules (339+ tools)
│       ├── __init__.py            # Tool registry
│       ├── search_execute.py      # Search/execute mode (4 tools)
│       │
│       ├── core.py                # Core operations
│       ├── project.py             # Project management
│       ├── project_advanced.py    # Advanced project ops
│       ├── project_complete.py    # Project completions
│       │
│       ├── timeline.py            # Timeline basics
│       ├── timeline_advanced.py   # Advanced timeline
│       ├── timeline_advanced2.py  # AI/ML timeline features
│       ├── timeline_complete.py   # Timeline completions
│       ├── timeline_operations.py # Timeline operations
│       │
│       ├── timelineitem_advanced.py  # Advanced clip ops
│       ├── timelineitem_advanced2.py # AI/ML clip features
│       ├── timeline_item_complete.py # Clip completions
│       │
│       ├── media.py               # Media Pool basics
│       ├── mediapool_advanced.py  # Advanced media ops
│       ├── mediapool_complete.py  # Media completions
│       ├── mediapool_selection.py # Selection & metadata
│       ├── mediapoolitem_advanced.py   # Clip properties
│       ├── mediapoolitem_complete.py   # Clip completions
│       ├── folder_navigation.py   # Folder operations
│       │
│       ├── color.py               # Color grading
│       ├── colorgroup_operations.py    # Color groups
│       ├── colorgroup_complete.py      # Group completions
│       │
│       ├── delivery.py            # Render basics
│       ├── render_settings.py     # Render configuration
│       ├── render_advanced.py     # Advanced rendering
│       │
│       ├── fusion.py              # Fusion operations
│       ├── fairlight.py           # Audio operations
│       ├── media_storage.py       # Media storage
│       │
│       ├── gallery.py             # Gallery basics
│       ├── gallery_advanced.py    # PowerGrades
│       ├── gallerystillalbum_complete.py  # Still albums
│       │
│       ├── graph.py               # Node graphs
│       ├── cache.py               # Cache management
│       ├── advanced.py            # Advanced features
│       │
│       ├── resolve_complete.py    # Resolve completions
│       ├── complete_api_coverage.py    # Remaining APIs
│       └── phase6_final.py        # Final completions
│
├── config-templates/              # Configuration examples
├── scripts/                       # Utility scripts
│   ├── mcp_resolve-cursor_start   # Cursor launcher
│   ├── mcp_resolve-claude_start   # Claude launcher
│   ├── mcp_resolve_launcher.sh    # Universal launcher
│   ├── check-resolve-ready.sh     # Pre-launch check
│   └── tests/                     # Test scripts
│
├── docs/                          # Documentation
│   ├── API_COVERAGE.md            # Complete API coverage
│   ├── API_PHASE4_SUMMARY.md      # Phase 4 details
│   ├── API_PHASE5_SUMMARY.md      # Phase 5 details
│   ├── FEATURES.md                # Feature list
│   ├── CHANGELOG.md               # Version history
│   └── TOOLS_README.md            # Tool documentation
│
├── install.sh / install.bat       # One-step installers
├── run-now.sh / run-now.bat       # Quick launchers
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

### Key Components

**Tool Proxy Layer** (`src/proxy.py`)
- Manages tool registration and execution
- Provides search/execute interface
- Handles parameter validation
- Supports both search_execute and full modes

**Tool Modules** (`src/tools/*.py`)
- Organized by functional area (editing, color, media, etc.)
- Each module provides `register_tools(mcp)` function
- Comprehensive error handling and logging
- Type-hinted for better IDE support

**Search/Execute Mode** (`src/tools/search_execute.py`)
- 4 core tools: search, execute, get_categories, list_tools
- Optimized for AI assistants with tool limits
- Natural language tool discovery

**Full Tool Mode**
- All 339+ tools exposed directly
- Better for auto-completion
- Ideal for unlimited tool clients

---

## 🔧 Troubleshooting

### Common Issues

**"Cannot connect to DaVinci Resolve"**
- ✅ Ensure DaVinci Resolve is running
- ✅ Check environment variables are set correctly
- ✅ Verify you're using the correct paths for your installation
- ✅ Try restarting both DaVinci Resolve and the MCP server

**"Client closed" or "Server disconnected"**
- ✅ Check that paths in configuration files are absolute, not relative
- ✅ Verify Python virtual environment is activated
- ✅ Ensure all dependencies are installed: `pip install -r requirements.txt`
- ✅ Check logs in `scripts/cursor_resolve_server.log`

**"Tool not found" or "Unknown tool"**
- ✅ In search_execute mode, use the search tool first to find available tools
- ✅ Tool names are case-sensitive
- ✅ Check `RESOLVE_MCP_MODE` environment variable is set correctly

**Performance Issues**
- ✅ Use search_execute mode for better performance with many tools
- ✅ Close unnecessary timelines and projects in DaVinci Resolve
- ✅ Check DaVinci Resolve isn't rendering in the background

### Platform-Specific Issues

**macOS:**
- Make sure scripts have execute permissions: `chmod +x *.sh`
- Check Console.app for Python-related errors
- Verify DaVinci Resolve.app is in /Applications

**Windows:**
- Use forward slashes (/) in configuration file paths
- Run Command Prompt as Administrator if permission errors occur
- Ensure Python is in your PATH

### Getting Help

1. **Check the logs**: `scripts/cursor_resolve_server.log`
2. **Run diagnostics**: `./scripts/check-resolve-ready.sh` (macOS) or `scripts\check-resolve-ready.bat` (Windows)
3. **Review documentation**: [docs/](docs/)
4. **Search existing issues**: [GitHub Issues](https://github.com/samuelgursky/davinci-resolve-mcp/issues)
5. **Create a new issue**: Include logs, OS version, DaVinci Resolve version, and configuration

---

## 👨‍💻 Development

### Running Tests

```bash
# Run test suite
python scripts/tests/test_improvements.py

# Run benchmarks
python scripts/tests/benchmark_server.py

# Create test timeline
python scripts/tests/create_test_timeline.py
```

### Adding New Tools

1. Create or edit a tool module in `src/tools/`
2. Implement your tool functions with proper docstrings
3. Add registration in the module's `register_tools(mcp)` function
4. Update `src/tools/__init__.py` to include your module
5. Test your tool using the search/execute interface

**Example:**
```python
# src/tools/my_feature.py
import logging

logger = logging.getLogger("davinci-resolve-mcp.tools.my_feature")

def my_new_tool(param1: str, param2: int) -> dict:
    """
    Description of what this tool does.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Result dictionary

    Example:
        >>> my_new_tool("test", 42)
        {"success": True, "result": "..."}
    """
    try:
        # Implementation here
        return {"success": True, "result": "..."}
    except Exception as e:
        logger.error(f"Error in my_new_tool: {e}")
        return {"success": False, "error": str(e)}

def register_tools(mcp):
    """Register tools with MCP server."""
    from ..proxy import get_proxy

    proxy = get_proxy()
    proxy.register_tool(
        "my_new_tool",
        my_new_tool,
        "category",
        "Short description",
        {
            "param1": {"type": "string", "description": "Param1 description"},
            "param2": {"type": "integer", "description": "Param2 description"}
        }
    )
    return 1
```

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and returns
- Include comprehensive docstrings with examples
- Add error handling and logging
- Test with both DaVinci Resolve Studio and Free versions

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- **Blackmagic Design** for DaVinci Resolve and its comprehensive API
- **Anthropic** for the Model Context Protocol and Claude
- **The MCP Community** for feedback and contributions
- **FastMCP Team** for the excellent Python SDK

---

## 📬 Contact & Support

**Author**: Samuel Gursky
**Email**: samgursky@gmail.com
**GitHub**: [@samuelgursky](https://github.com/samuelgursky)

**Project**: [github.com/samuelgursky/davinci-resolve-mcp](https://github.com/samuelgursky/davinci-resolve-mcp)

---

## 🗺️ Roadmap

- ✅ **Phase 1-5**: Core API coverage (71%)
- ✅ **Phase 6**: 100% API coverage (COMPLETE!)
- 🔄 **Future**: Enhanced AI integrations
- 🔄 **Future**: Web-based control interface
- 🔄 **Future**: Plugin ecosystem
- 🔄 **Future**: Advanced batch automation
- 🔄 **Future**: Real-time collaboration features

---

## ⭐ Star History

If you find this project useful, please consider giving it a star on GitHub!

---

**Built with ❤️ for the DaVinci Resolve and AI communities**

*Last updated: 2025-10-20*
