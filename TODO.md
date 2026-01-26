# Private Project TODO Notes


## Table of Contents

[kanban](#kanban)
[devnotes](#developer-notes)


[[hsb3-custom-plugins feedback]](#hsb3-custom-plugins-feedback)


---
## Kanban

### **backlog**
- [ ] add test w/ early exit for non-existent db 

### **in progress**


## **completed**

---

## Developer Notes

### brain dump

- snowflake connection (env/asst).. maybe rt later
- schema explore; query write/exec
  - default all schema/tables; otherwise constrainer
    - DB_AGENT_ALLOWED_SCHEMAS=[*]
    - DB_AGENT_ALLOWED_TABLES=[*]
- for dev, CORS_ORIGINS=[*]
  - ?? WARNING/ERROR if env indicates not dev and no cors restrictions
- build on langchain v1 chassis; avoid deepagents bloat
  - nice to have, maybe later:
    - backend protocol (could connect to sprites)
      - filesystem .. 

- easiest is to drive agent via langgraphi api; after compiling server
  - if one shot or don't want to deal with server stuff; can control with lightweight cli | repl using inmem versions of checkpointer + store

- poc for jerry.. terminal over web ui likely
    - [ ] check on universal 


agent structure:
    --- configurable items ----
    metadata:
    
    config_schema: base, env settings + defaults
    context_schema:  variable parameters for variants/mutants
      - here we set runtime arugments
    input/output/state_schema:
    ---
    models: types/structured-tools
    state: input|internal|output
    utils: as needed
    tools/:  sql, eval, think, 
    prompts/: load from file (.py)
    graph: agent generator function
    
    langgraph.json: config file for langgraph server build
    pyproject.toml: 
    .env/.env.example: 
----

- [ ] scaffold basic langchain (v1) agent
- [ ] add tools for snowflake access; some local instance for quick test
  - [ ] guardrails on sql tools
    - [ ] by prompting
    - [ ] programmatic restriction/guard

always in the background:
- should i be adding something to config and/or context
- how can i break this thing?

----

will have:
- agent
- repl

---
uv init --no-readme --name agent-snowflake
uv add (deps)
add deps:
langchain langgraph
langchain-anthropic langchain-openai 
? langchain-google-genai
snowflake-connector-python
python.env

### makefile commands

[help] -- default
install deps (incl. dev). uv sync --all-groups
seed test-db
start/stop test-db
dev: start langraph server
dev-h start headless
lint
typecheck
test
check
clean


### snowflake emulator
pip install "snowflake-snowpark-python[localtest]"
https://docs.snowflake.com/en/developer-guide/snowpark/python/testing-locally
>>> license required . .. meh

---

```py

# roll your own tools ...

pip install "snowflake-sqlalchemy"

from sqlalchemy import create_engine, text
from snowflake.sqlalchemy import URL

engine = create_engine(URL(
    account="ACCT_LOCATOR_OR_IDENTIFIER",
    user="AGENT_USER",
    password="***",
    warehouse="DEV_WH",
    database="AGENT_DEV",
    schema="SANDBOX",
    role="AGENT_ROLE",
))

with engine.connect() as conn:
    rows = conn.execute(text("select current_version(), current_warehouse(), current_role()")).all()
    print(rows)
```

### stock quesations for 


```
Answer below questions, one at a time:
“For each billing country, what is total invoice revenue, number of invoices, and average invoice total? Rank countries by total revenue (desc) and return the top 10.”
“List the top 10 artists by total sales revenue. For each artist, include total revenue, number of distinct tracks sold, and number of distinct customers.”
“For each customer, compute: first purchase date, last purchase date, total spend, and number of distinct purchase months. Then return the 20 customers with the most distinct purchase months (tie-break by total spend).”
```
⸻

### repl (client) requirements

- client that connects to running langgraph server
  - local dev server preserves/persists state in a local checkpointer
  - if we want store we'll have to set up inmem or local (sqlite store); low priority
- ui is console/terminal (rich + prompttoolkit)
- ui features
  - list/select agents
  - list/start/select (resume) threads
  - handle context blocks (see: /Users/henry/Developer/_SANDBOX/zArchive/langchain_v1/docs/repl/langgraph_cli.py)
  - handle HITL components
  - handle rendering of fenced items? like python, js, etc
  - markdown syntax highlighting (including table rendering)
- create new agent/asssitant?
  - display/set configurable items?
    - ideally would list limited options for some items like provider/model

**patterns**
- one way dependencies ---> no spaghetti code
- 6 layers -

**open questions**
- how and where to handle REPL config? toml, json, ... ?  where ? 
 
 **decisions**
 - use langgraph-sdk for client
 - add logger for repl/client>repl-client.log; direct server logs to server.log

---

? config
? register tool signatures

1. http client + logger
2. tooling: parsers
3. app state
4. handle stream
5. ui render stream
6. commands
7. loop loop

how would we controlled all this with langgraph? pydantic graph?

Minimal UML set that actually works (recommended)
	1.	Component diagram: boundaries + interfaces
	2.	Sequence diagram: one turn (with loop/alt)
	3.	State machine: REPL session control + cancellation
	4.	Class diagram: message/event/state schemas

---




### hsb3-custom-plugins feedback
#### work-documentation

- [ ] add hooks to remind
  - [ ] use subagents if more than 3 docs
  - [ ] frontmatter convention and filenameing
- [ ] add hooks to check for rule violations

```yaml
---
doc_id:CC-YYYY-NNN
title: Brief description
date: YYYY-MM-DD
type: planning|solution|investigation|status|summary
project: app1|app2|...
focus: ...
status: draft|complete
tags: [stategraph, repl, ...]
---
```

#### learning tasks
- [ ] update reference docs and norms for:
  - [ ] langgraph agent development
  - [ ] langgraph workflow development
  - [ ] monorepos
  - [ ] building tui with textual
  - [ ] designing repl
  - [ ] available langgraph ecosystem middlewares


---

**references**
- prebuilt middlweare: https://docs.langchain.com/oss/python/langchain/middleware/built-in
- textual/repl inspo: https://github.com/batrachianai/toad
- textual/markdown browser: https://github.com/Textualize/frogmouth
- textual chat app: https://github.com/darrenburns/elia
- rich/console chat repls:
  - langrepl


- [GitHub - lerocha/chinook-database](https://github.com/lerocha/chinook-database)
- [LangChain Middleware Documentation](https://python.langchain.com/docs/langchain/agents/middleware)
- [LangGraph Persistence](https://python.langchain.com/docs/langgraph/persistence)
- [Human-in-the-Loop Guide](https://python.langchain.com/docs/langchain/human-in-the-loop)
- [Model Profiles](https://python.langchain.com/docs/langchain/models#model-profiles)
- [LangGraph SDK Docs](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/)
  - PyPI: https://pypi.org/project/langgraph-sdk/



#### follow-ups
**public data sources**

https://ourworldindata.org/
https://www.cms.gov/data-research/statistics-trends-and-reports/national-health-expenditure-data/age-and-sex
https://archive.ics.uci.edu/dataset/891/cdc+diabetes+health+indicators
https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008

```sql
-- Replace with any OWID grapher chart slug you like
-- You can discover slugs by browsing OWID charts and copying the /grapher/<slug> part.

SELECT *
FROM read_csv_auto('https://ourworldindata.org/grapher/annual-healthcare-expenditure-per-capita.csv')
LIMIT 50;

```
