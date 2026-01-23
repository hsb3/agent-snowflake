#!/bin/bash
# Template script for creating common config files for LangGraph agent projects
# Usage: ./create-config-files.sh <agent-module-name>

set -e

MODULE_NAME="${1:-agent}"

echo "Creating config files for: $MODULE_NAME"

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/
venv/
ENV/
env/

# Environment Variables
.env
.env.local

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/
*.cover

# LangGraph
.langgraph/

# Logs
*.log
EOF

# Create langgraph.json
cat > langgraph.json << EOF
{
  "graphs": {
    "agent": "./src/${MODULE_NAME}/graph.py:graph"
  },
  "env": ".env"
}
EOF

# Create basic .env.example
cat > .env.example << 'EOF'
# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key

# Model Configuration
# Options: anthropic, openai, google
MODEL_PROVIDER=anthropic
# Model names: claude-sonnet-4-5-20250929, gpt-4o, gemini-2.0-flash-exp, etc.
MODEL_NAME=claude-sonnet-4-5-20250929

# Development
ENVIRONMENT=development

# Add your specific environment variables here
EOF

echo "Config files created!"
echo "  - .gitignore"
echo "  - langgraph.json"
echo "  - .env.example (customize for your project)"
