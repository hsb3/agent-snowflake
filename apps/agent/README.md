# agent-snowflake

Various LangGraph agents.  Primary interaction via LangGraph Dev Server.

## Makefile Commands

```bash
  # setup
  make install        - Install dependencies with uv
  make setup-test-db  - Create test SQLite database with stub TPC-H data
  make setup-chinook  - Download Chinook database (digital media store, 11 tables)
  
  # langgraph dev server
  make dev            - Start LangGraph dev server with Studio UI
  make dev-server     - Start LangGraph dev server without browser (for REPL)
  
  
  # development commands
  make test           - Run all tests with pytest
  make test-fast      - Run tests excluding slow tests
  make format         - Format code with ruff
  make lint           - Lint code with ruff
  make type-check     - Type check with ty
  make clean          - Remove generated files and caches
```

See `Makefile` for additional commands (setup-chinook, test-fast, lint, clean).

## Agent Variants

- **agent** - Core SQL agent with LangChain toolkit
- **agent_minimal** - Adds guardrails and context controls
- **agent_enhanced** - Full featured with extended tooling

## Preview LangGraph Dev Server

<table>
  <tr>
    <td><img src="../../docs/assets/agent_core.png" alt="Agent Core" width="400"/></td>
    <td><img src="../../docs/assets/agent_enhanced.png" alt="Agent Enhanced" width="400"/></td>
  </tr>
  <tr>
    <td><img src="../../docs/assets/agent_min.png" alt="Agent Minimal" width="400"/></td>
    <td><img src="../../docs/assets/entry.png" alt="Entry Point" width="400"/></td>
  </tr>
  <tr>
    <td colspan="2" align="center"><img src="../../docs/assets/schema_extras.png" alt="Schema Extras" width="400"/></td>
  </tr>
</table>



## Notes

- LANGSMITH_API_KEY optional
- API docs at localhost:2024/docs
- Viewing Safari requires `--tunnel` flag
- Config precedence: defaults → environment → overrides

---

### Try below prompts with SQL agents
```
Answer below questions, one at a time:

“For each billing country, what is total invoice revenue, number of invoices, and average invoice total? Rank countries by total revenue (desc) and return the top 10.”


“List the top 10 artists by total sales revenue. For each artist, include total revenue, number of distinct tracks sold, and number of distinct customers.”


“For each customer, compute: first purchase date, last purchase date, total spend, and number of distinct purchase months. Then return the 20 customers with the most distinct purchase months (tie-break by total spend).”

```

---

**reference projects**

- textual/repl inspo: https://github.com/batrachianai/toad
- textual chat app: https://github.com/darrenburns/elia



