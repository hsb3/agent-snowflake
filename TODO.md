# Private Project TODO Notes

## Kanban

### **backlog**

- [ ] notes/obs in langg
- [ ] prebuilt middlweare: https://docs.langchain.com/oss/python/langchain/middleware/built-in
- [ ] anything else? 
- [ ] 

### **in progress**

## **completed**

---

## Developer Notes

### brain dumpt
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
    config: base, env settings + defaults
    context:  variable parameters for variants/mutants
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

### LangGraph Rules



### makefile commands

[help] -- default

install deps (incl. dev). uv sync --all-groups
start snowflake emulator
stop snowflake emulator
dev: start langraph server
dev-n start langgraph server with --no-browser

lint
typecheck
test-unit (unit only)
test
qa (all above)

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