#!/bin/bash
# Template script for setting up a LangChain/LangGraph agent project with uv
# Usage: ./setup-langgraph-agent.sh <project-name> [python-version]

set -e

PROJECT_NAME="${1:-agent-project}"
PYTHON_VERSION="${2:-3.12}"

echo "Setting up LangGraph agent project: $PROJECT_NAME"
echo "Using Python: $PYTHON_VERSION"

# Initialize uv project
echo "Initializing uv project..."
uv init --no-readme --name "$PROJECT_NAME"

# Install Python version
echo "Installing Python $PYTHON_VERSION..."
uv python install "$PYTHON_VERSION"

# Install core dependencies
echo "Installing dependencies..."
uv add langchain langgraph langchain-anthropic langchain-openai langchain-google-genai python-dotenv

echo "Project setup complete!"
echo "Next steps:"
echo "  1. Add your specific database connector (e.g., snowflake-connector-python)"
echo "  2. Create src/ directory structure"
echo "  3. Copy .env.example and configure"
