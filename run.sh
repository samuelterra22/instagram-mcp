#!/usr/bin/env bash
# Launcher do Instagram MCP p/ Claude Code. cwd = repo root (import relativo + .env).
cd "$(dirname "$0")"
exec .venv/bin/python -m src.instagram_mcp_server
