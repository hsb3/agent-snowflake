"""Tool-specific rendering handlers for subgraph approach.

This module provides render nodes for different tool types from agent-snowflake.
Each tool handler converts tool call data into appropriate render queue items
with proper formatting hints for the UI layer.

Tool Coverage:
    SQL Tools (LangChain SQLDatabaseToolkit):
        - sql_db_query: Execute SELECT queries → SQL syntax highlighting
        - sql_db_schema: Get table schemas → Table list display
        - sql_db_list_tables: List available tables → Simple info panel
        - sql_db_query_checker: Validate SQL → SQL syntax highlighting

    Interactive Tools:
        - AskUserQuestion: User prompts with options → Interactive display

    Generic Fallback:
        - Unknown tools → JSON args display

Render Strategy:
    Tool handlers don't render directly. Instead, they add structured items to
    render_queue with "display" hints. The render_output_node() in rendering.py
    reads these hints and dispatches to appropriate Rich-based renderers.

Display Format Types:
    - "sql": SQL code with syntax highlighting
    - "schema": Formatted table names list
    - "list_tables": Simple info about table listing
    - "question": Interactive Q&A prompt
    - (none): Generic JSON args panel
"""


def render_sql_tool_node(state: dict) -> dict:
    """Render SQL-related tool calls with appropriate formatting.

    Handles all SQL tools from LangChain's SQLDatabaseToolkit:
    - sql_db_query: Show query with SQL syntax highlighting
    - sql_db_query_checker: Show query being validated with SQL highlighting
    - sql_db_schema: Show list of tables being queried for schema
    - sql_db_list_tables: Show simple info panel about table listing

    Each tool type gets appropriate "display.format" hint:
    - sql_db_query/checker → format="sql" (syntax highlighting)
    - sql_db_schema → format="schema" (table list)
    - sql_db_list_tables → format="list_tables" (info panel)

    Args:
        state: Subgraph state with current_chunk containing tool call

    Returns:
        Updated state with render_queue entry containing tool display hints

    Example render_queue item (sql_db_query):
        {
            "type": "tool_call",
            "tool": {
                "name": "sql_db_query",
                "args": {"query": "SELECT * FROM customers"},
                "display": {
                    "format": "sql",
                    "query": "SELECT * FROM customers"
                }
            }
        }
    """
    current_chunk = state.get("current_chunk")
    render_queue = list(state.get("render_queue", []))

    if not current_chunk:
        return state

    event_type, data = current_chunk

    # Extract tool call from messages/complete
    if isinstance(data, list) and data:
        message = data[-1]
        if isinstance(message, dict):
            tool_calls = message.get("tool_calls", [])
            if tool_calls:
                for tool_call in tool_calls:
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("name", "")
                        tool_args = tool_call.get("args", {})

                        # Format SQL tools
                        if tool_name in ("sql_db_query", "sql_db_query_checker"):
                            # SQL query or query checker - show SQL with highlighting
                            query = tool_args.get("query", "")
                            render_queue.append(
                                {
                                    "type": "tool_call",
                                    "tool": {
                                        "name": tool_name,
                                        "args": tool_args,
                                        "display": {
                                            "format": "sql",
                                            "query": query,
                                        },
                                    },
                                }
                            )
                        elif tool_name == "sql_db_schema":
                            # Schema query - show table names
                            tables = tool_args.get("table_names", "")
                            # Handle both string and list formats
                            if isinstance(tables, str):
                                table_list = [t.strip() for t in tables.split(",") if t.strip()]
                            else:
                                table_list = tables if isinstance(tables, list) else []
                            render_queue.append(
                                {
                                    "type": "tool_call",
                                    "tool": {
                                        "name": tool_name,
                                        "args": tool_args,
                                        "display": {
                                            "format": "schema",
                                            "tables": table_list,
                                        },
                                    },
                                }
                            )
                        elif tool_name == "sql_db_list_tables":
                            # List tables - simple display
                            render_queue.append(
                                {
                                    "type": "tool_call",
                                    "tool": {
                                        "name": tool_name,
                                        "args": tool_args,
                                        "display": {
                                            "format": "list_tables",
                                        },
                                    },
                                }
                            )

    return {
        **state,
        "render_queue": render_queue,
    }


def render_question_tool_node(state: dict) -> dict:
    """Render AskUserQuestion tool with interactive prompt formatting.

    Formats user questions with options for display. Currently shows as a panel
    with question and bullet list of options. Future Phase 3 enhancement will
    add arrow-key navigation for option selection.

    Display format: format="question" with question text and options list.

    Args:
        state: Subgraph state with current_chunk containing AskUserQuestion call

    Returns:
        Updated state with render_queue entry for interactive question

    Example render_queue item:
        {
            "type": "tool_call",
            "tool": {
                "name": "AskUserQuestion",
                "args": {
                    "question": "Which region?",
                    "options": ["ASIA", "EUROPE", "AMERICAS"]
                },
                "display": {
                    "format": "question",
                    "question": "Which region?",
                    "options": ["ASIA", "EUROPE", "AMERICAS"]
                }
            }
        }
    """
    current_chunk = state.get("current_chunk")
    render_queue = list(state.get("render_queue", []))

    if not current_chunk:
        return state

    event_type, data = current_chunk

    # Extract tool call from messages/complete
    if isinstance(data, list) and data:
        message = data[-1]
        if isinstance(message, dict):
            tool_calls = message.get("tool_calls", [])
            if tool_calls:
                for tool_call in tool_calls:
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("name", "")
                        if tool_name == "AskUserQuestion":
                            tool_args = tool_call.get("args", {})
                            question = tool_args.get("question", "")
                            options = tool_args.get("options", [])

                            render_queue.append(
                                {
                                    "type": "tool_call",
                                    "tool": {
                                        "name": tool_name,
                                        "args": tool_args,
                                        "display": {
                                            "format": "question",
                                            "question": question,
                                            "options": options,
                                        },
                                    },
                                }
                            )

    return {
        **state,
        "render_queue": render_queue,
    }


def render_generic_tool_node(state: dict) -> dict:
    """Render generic tool call for unknown/unhandled tools.

    Fallback handler for tools without custom rendering. Displays tool name and
    args as JSON in a yellow panel. This ensures all tools are visible even if
    they don't have specialized formatting.

    No "display" format specified - rendering.py uses default JSON args display.

    Args:
        state: Subgraph state with current_chunk containing tool call

    Returns:
        Updated state with render_queue entry for generic tool display

    Example render_queue item:
        {
            "type": "tool_call",
            "tool": {
                "name": "custom_tool",
                "args": {"param1": "value1", "param2": 123}
            }
        }

    Note:
        When adding a new tool type, create a custom handler and update
        route_by_tool_name() in tool_router.py to route to it instead of
        falling back to this generic handler.
    """
    current_chunk = state.get("current_chunk")
    render_queue = list(state.get("render_queue", []))

    if not current_chunk:
        return state

    event_type, data = current_chunk

    # Extract tool call from messages/complete
    if isinstance(data, list) and data:
        message = data[-1]
        if isinstance(message, dict):
            tool_calls = message.get("tool_calls", [])
            if tool_calls:
                for tool_call in tool_calls:
                    if isinstance(tool_call, dict):
                        render_queue.append(
                            {
                                "type": "tool_call",
                                "tool": tool_call,
                            }
                        )

    return {
        **state,
        "render_queue": render_queue,
    }
