# LangGraph Agent Project Templates

Bash scripts for quickly scaffolding LangChain/LangGraph agent projects with uv.

## Usage

### Complete Setup (New Project)

```bash
# 1. Setup base project
./setup-langgraph-agent.sh my-agent-project 3.12

# 2. Create agent structure
cd my-agent-project
./create-agent-structure.sh agent_myproject

# 3. Create config files
./create-config-files.sh agent_myproject
```

### Individual Scripts

**setup-langgraph-agent.sh** - Initialize uv project and install core dependencies
```bash
./setup-langgraph-agent.sh <project-name> [python-version]
```

**create-agent-structure.sh** - Create agent module directory structure
```bash
./create-agent-structure.sh <agent-module-name>
```

**create-config-files.sh** - Generate .gitignore, langgraph.json, .env.example
```bash
./create-config-files.sh <agent-module-name>
```

## Customization

After running these scripts, customize for your specific use case:

1. Add database-specific dependencies (e.g., `uv add snowflake-connector-python`)
2. Update `.env.example` with your required environment variables
3. Implement your agent logic in the generated module files

## Module Structure

The scripts create this structure:

```
src/
└── <module-name>/
    ├── __init__.py
    ├── config.py      # Base env settings + defaults
    ├── context.py     # Variable parameters for variants
    ├── models.py      # Types/structured-tools
    ├── state.py       # Input|internal|output state
    ├── utils.py       # Utilities
    ├── graph.py       # Agent generator function
    ├── tools/         # Agent tools
    │   └── __init__.py
    └── prompts/       # Prompt templates
        └── __init__.py
```
