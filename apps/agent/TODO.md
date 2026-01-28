# Private Project TODO Notes

## Kanban

### **backlog**

- [x] confirm whether or not can use sqlite checkpointers instead of pickled dicts for dev server usage
- [x] add a variable to .env / .env.example for which llm to use for testing
- [ ] rename package from "agent_snowflake" to "agent".  replace all references of "agent_snowflake" and "snowflake_agent" with just "agent"




### **in progress**

## **completed**

---

## Developer Notes


### using sqlite for checkpointers and stores

> You cannot configure langgraph dev server to use SQLiteSaver or SQLiteStore via langgraph.json \
To enable using such while using langgraph dev server, you must: \
- create factory functions for each checkpointer + store; use async version
- assign the checkpointer and store in the graph builder defintions

Now maybe we want to handle different situations:
1. default local langgraph dev behavior
2. local langgraph dev behavior ride with
  - AsyncSqliteSaver
  - AsyncSqliteStore w/o embeddings/vector search
  - AsyncSqliteStore w/ embeddings/vector search
3. configuration for deployment (which could be equivalent to 1; but could also be different)

Simple way to do this is to create a base factory function with options like:
- override_default_checkpointer: bool
- override_default_store
- enable_sqlite_store_embeddings

The list could go on an on.  Rather than building super complex functions to handle a lot of different situations that you might not even use, it's probably better to just know that you can do this and modify the factory functions and langgraph server configuration file (`langgraph.json`) for whatever you're doing in the moment. 


```json
{
  "checkpointer": {
    "ttl": {
      "default_ttl": 43200,
      "sweep_interval_minutes": 10
    },
    "serde": {
      "pickle_fallback": false,
      "allowed_json_modules": ["datetime", "uuid", "collections"]
    }
  },
  "store": {
    "ttl": {
      "default_ttl": 10080,
      "refresh_on_read": true,
      "sweep_interval_minutes": 60
    },
    "index": {
      "embed": "openai:text-embedding-3-small",
      "dims": 1536,
      "fields": ["content"]
    }
  }
}


```