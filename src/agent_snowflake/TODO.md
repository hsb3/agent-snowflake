# Private Project TODO Notes

## Kanban

### **backlog**

- [ ] notes/obs in langg

### **in progress**

## **completed**

---

## Developer Notes


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