@echo off
REM Wrapper script to launch the DaVinci Resolve MCP server
REM This ensures we use the correct Python interpreter from the venv

set SCRIPT_DIR=%~dp0
set ROOT_DIR=%SCRIPT_DIR%..\
set VENV_PYTHON=%ROOT_DIR%venv\Scripts\python.exe
set SERVER_SCRIPT=%ROOT_DIR%src\resolve_mcp_server.py

"%VENV_PYTHON%" "%SERVER_SCRIPT%"
