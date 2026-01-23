# agent-snowflake


3 example langchain/langgraph agents to experiment with.

- `agent` - Basic agent; just uses sql
- `agent_minimal` - more controls
- `agent_enhanced` - more extenders

## Architecture Diagrams

<table>
  <tr>
    <td><img src="docs/assets/agent_core.png" alt="Agent Core" width="400"/></td>
    <td><img src="docs/assets/agent_enhanced.png" alt="Agent Enhanced" width="400"/></td>
  </tr>
  <tr>
    <td><img src="docs/assets/agent_min.png" alt="Agent Minimal" width="400"/></td>
    <td><img src="docs/assets/entry.png" alt="Entry Point" width="400"/></td>
  </tr>
  <tr>
    <td colspan="2" align="center"><img src="docs/assets/schema_extras.png" alt="Schema Extras" width="400"/></td>
  </tr>
</table>

## Getting Started

Use Makefile to get started quickly.

Available commands:
  make install        - Install dependencies with uv
  make setup-fakesnow - Stub sqlite db
  make setup-chinook  - Chinook sqlite db
  make dev            - Start LangGraph dev server with Studio UI\
  make test           - Run all tests with pytest
  make test-fast      - Run tests excluding slow tests
  make format         - Format code with ruff
  make lint           - Lint code with ruff
  make type-check     - Type check with ty
  make clean          - Remove generated files and caches

----

NOTES:
- LANGSMITH_API_KEY is optional 
- Swagger-ish docs available at localhost:2024/docs
- site won't open in safari unless you use --tunnel switch

----

Parameters set: defaults > environment > config overrides


--- 

