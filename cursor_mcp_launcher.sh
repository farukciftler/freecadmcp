#!/bin/bash

# FreeCAD MCP Launcher for Cursor
# This script ensures the project runs in the correct directory as a Python module.

PROJECT_DIR="/Users/farukciftler/Documents/projects/freecadmcp"

# Navigate to project directory
cd "$PROJECT_DIR" || exit 1

# Add current directory to Python path (for relative imports to work)
export PYTHONPATH="$PROJECT_DIR"

# Start the MCP Server via Standard I/O
exec python3 -m server.main