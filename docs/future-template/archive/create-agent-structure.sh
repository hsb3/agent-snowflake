#!/bin/bash
# Template script for creating LangGraph agent directory structure
# Usage: ./create-agent-structure.sh <agent-module-name>

set -e

MODULE_NAME="${1:-agent}"

echo "Creating directory structure for: $MODULE_NAME"

# Create directory structure
mkdir -p "src/${MODULE_NAME}/{tools,prompts}"

# Create module files
touch "src/${MODULE_NAME}/__init__.py"
touch "src/${MODULE_NAME}/config.py"
touch "src/${MODULE_NAME}/context.py"
touch "src/${MODULE_NAME}/models.py"
touch "src/${MODULE_NAME}/state.py"
touch "src/${MODULE_NAME}/utils.py"
touch "src/${MODULE_NAME}/graph.py"
touch "src/${MODULE_NAME}/tools/__init__.py"
touch "src/${MODULE_NAME}/prompts/__init__.py"

echo "Directory structure created!"
echo ""
echo "Module structure:"
echo "  config.py   - Base env settings + defaults"
echo "  context.py  - Variable parameters for variants"
echo "  models.py   - Types/structured-tools"
echo "  state.py    - Input|internal|output state"
echo "  utils.py    - Utilities"
echo "  graph.py    - Agent generator function"
echo "  tools/      - Agent tools"
echo "  prompts/    - Prompt templates"
