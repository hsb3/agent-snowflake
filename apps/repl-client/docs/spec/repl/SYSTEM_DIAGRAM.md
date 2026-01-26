# REPL Client System Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              REPL CLIENT                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────┐              ┌─────────────────────┐              │
│   │   Classic REPL      │              │    Textual TUI      │              │
│   │   __main__.py       │              │    tui/app.py       │              │
│   │                     │              │                     │              │
│   │   Simple terminal   │              │   Rich terminal UI  │              │
│   │   input() based     │              │   Widgets/Modals    │              │
│   └──────────┬──────────┘              └──────────┬──────────┘              │
│              │                                    │                         │
│              └────────────────┬───────────────────┘                         │
│                               │                                             │
│                               ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        SHARED CORE                                  │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│   │  │   Client    │  │  Streaming  │  │   Session   │  │  Commands  │  │   │
│   │  │  (Layer 1)  │  │  (Layer 4)  │  │  (Layer 3)  │  │  (Layer 7) │  │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                               │                                             │
└───────────────────────────────┼─────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   LangGraph Server    │
                    │   localhost:2024      │
                    │                       │
                    │   - Agents/Assistants │
                    │   - Threads           │
                    │   - SSE Streaming     │
                    └───────────────────────┘
```

## Layer Architecture (Classic REPL)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Layer 8: Orchestration                                      __main__.py    │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ REPLLoop                                                                │ │
│ │ - run() → _run_async()        Single event loop for all async ops      │ │
│ │ - _startup()                  Connect, list agents, create thread      │ │
│ │ - _handle_input_async()       Route commands vs messages               │ │
│ │ - _send_message()             Stream to agent, process response        │ │
│ │ - _handle_stream()            Render ParsedChunks                      │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 7: Commands                                      commands/           │
│ ┌──────────────────────────────────┐ ┌──────────────────────────────────┐  │
│ │ CommandRegistry                  │ │ CommandHandlers                  │  │
│ │ - register(name, handler)        │ │ - help, exit, agents, threads    │  │
│ │ - execute(name, args)            │ │ - new, info, clear, session      │  │
│ └──────────────────────────────────┘ └──────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 6: Rendering                                              ui/        │
│ ┌──────────────────────────────────┐ ┌──────────────────────────────────┐  │
│ │ Renderer                         │ │ ToolRenderRegistry               │  │
│ │ - render_panel()                 │ │ - Format tool previews           │  │
│ │ - render_code()                  │ │ - Custom formatters per tool     │  │
│ │ - render_table()                 │ │                                  │  │
│ └──────────────────────────────────┘ └──────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 5: HITL                                          streaming/hitl.py   │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ HITLHandler                                                             │ │
│ │ - handle_interrupt(interrupt, session)  Show approval prompt            │ │
│ │ - _format_tool_preview()                Format tool for display         │ │
│ │ - _build_resume_command()               Build resume command dict       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 4: Stream Processing                            streaming/handler.py │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ StreamHandler                                                           │ │
│ │ - process_stream(chunks)        Generator: yields ParsedChunk          │ │
│ │ - _extract_text_delta()         Cumulative → delta extraction          │ │
│ │ - _buffer_tool_call()           Accumulate partial_json                │ │
│ │ - _parse_interrupt()            Detect __interrupt__ in updates        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 3: Session State                                 core/session.py     │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ SessionState                    Ephemeral state, cleared on exit        │ │
│ │ - current_thread_id             Current conversation thread             │ │
│ │ - current_assistant_id          Current agent UUID                      │ │
│ │ - session_tokens                Token usage tracking                    │ │
│ │ - set_thread(), set_agent()     Update current context                  │ │
│ │ - track_tokens()                Accumulate usage                        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 2: Parsers                                        core/parsers.py    │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ extract_text_delta(prev, current)   String delta extraction             │ │
│ │ ToolCall(id, name, args)            Tool call data                      │ │
│ │ Usage(input, output, total)         Token usage data                    │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 1: HTTP Client                                    core/client.py     │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ LangGraphClient                 Wraps langgraph-sdk                     │ │
│ │ - connect()                     Health check                            │ │
│ │ - list_agents(), get_agent()    Agent operations                        │ │
│ │ - create_thread(), get_thread() Thread operations                       │ │
│ │ - stream_message()              SSE streaming (messages + updates)      │ │
│ │ - resume_after_interrupt()      HITL resume                             │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 0: Logging                                        core/logging.py    │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ get_logger(name)                Client-side logging to .repl/           │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow: Message → Response

```
┌──────────────┐
│ User types:  │
│ "Hello"      │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ REPLLoop._handle_input_async("Hello")                                    │
│ - Not a command (no "/")                                                 │
│ - Route to _send_message()                                               │
└──────────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ REPLLoop._send_message("Hello")                                          │
│ - Verify thread_id and assistant_id exist                                │
│ - Display "You: Hello"                                                   │
│ - Call client.stream_message()                                           │
└──────────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ LangGraphClient.stream_message(thread_id, "Hello", assistant_id)         │
│                                                                          │
│ POST /threads/{thread_id}/runs/stream                                    │
│ Body: {"input": {"messages": [{"role": "user", "content": "Hello"}]}}   │
│ stream_mode: ["messages", "updates"]  ← Dual mode for HITL              │
└──────────────────────────────────────────────────────────────────────────┘
       │
       │ SSE Stream (Server-Sent Events)
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Server yields events:                                                    │
│                                                                          │
│ event: metadata                                                          │
│ data: {"run_id": "..."}                                                 │
│                                                                          │
│ event: messages/partial                                                  │
│ data: [{"id": "msg-1", "content": [{"type": "text", "text": "Hi"}]}]   │
│                                                                          │
│ event: messages/partial                                                  │
│ data: [{"id": "msg-1", "content": [{"type": "text", "text": "Hi there"}]}]│
│       ↑ Cumulative text (not deltas!)                                   │
│                                                                          │
│ event: messages/complete                                                 │
│ data: [{"id": "msg-1", "content": "Hi there!", "usage_metadata": {...}}]│
│                                                                          │
│ event: updates                                                           │
│ data: {"agent": {...}}  ← Or {"__interrupt__": [...]} if HITL          │
└──────────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ StreamHandler.process_stream(chunks)                                     │
│                                                                          │
│ For each (event_type, data):                                             │
│                                                                          │
│   "messages/partial" → Extract text delta                                │
│     prev_text: "Hi"                                                      │
│     curr_text: "Hi there"                                                │
│     delta: " there"  ← Only the new part                                │
│     yield ParsedChunk(TEXT_DELTA, text_delta=" there")                  │
│                                                                          │
│   "messages/complete" + tool_calls → yield TOOL_CALL_COMPLETE           │
│                                                                          │
│   "updates" + __interrupt__ → yield ParsedChunk(INTERRUPT, ...)         │
│                                                                          │
│   usage_metadata → yield ParsedChunk(USAGE, ...)                        │
└──────────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ REPLLoop._handle_stream(parsed_chunks)                                   │
│                                                                          │
│ async for chunk in parsed_chunks:                                        │
│   match chunk.chunk_type:                                                │
│     TEXT_DELTA → print(chunk.text_delta, end="")  ← Streaming output    │
│     TOOL_CALL_COMPLETE → log tool call                                   │
│     INTERRUPT → HITLHandler.handle_interrupt()                          │
│     USAGE → session.track_tokens()                                       │
└──────────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│ Terminal:    │
│ Agent: Hi    │
│ there!       │
└──────────────┘
```

## HITL (Human-in-the-Loop) Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Agent wants to execute tool: sql_db_query                                │
│ Server sends __interrupt__ in "updates" stream                          │
└──────────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ StreamHandler detects __interrupt__                                      │
│                                                                          │
│ event: updates                                                           │
│ data: {                                                                  │
│   "__interrupt__": [{                                                    │
│     "value": {                                                           │
│       "tool": "sql_db_query",                                           │
│       "args": {"query": "SELECT * FROM users"}                          │
│     },                                                                   │
│     "when": "during"                                                     │
│   }]                                                                     │
│ }                                                                        │
│                                                                          │
│ yield ParsedChunk(INTERRUPT, interrupt=Interrupt(...))                  │
└──────────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ REPLLoop calls HITLHandler.handle_interrupt(interrupt, session)          │
│                                                                          │
│ ┌──────────────────────────────────────────────────────────────────────┐ │
│ │ Tool: sql_db_query                                                   │ │
│ │ Args:                                                                │ │
│ │   query: SELECT * FROM users                                         │ │
│ │                                                                      │ │
│ │ Approve? [y/n]:                                                      │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
       │
       │ User types: y
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ HITLHandler returns command: {"resume": {"approve": True}}               │
│                                                                          │
│ REPLLoop calls client.resume_after_interrupt(thread_id, agent_id, cmd)  │
└──────────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Server executes tool, resumes agent                                      │
│ Returns new SSE stream with tool result + continuation                  │
└──────────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ REPLLoop._handle_stream() called recursively                             │
│ Processes resumed stream same as original                                │
└──────────────────────────────────────────────────────────────────────────┘
```

## TUI Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REPLApp (Textual App)                            │
│                                                                             │
│  Lifecycle: on_mount() → on_ready() → Event Loop → on_shutdown()          │
│  Key Bindings: F2 (agents), F3 (threads), F4 (sidebar), Ctrl+C (quit)     │
└─────────────────────────────────────────────────────────────────────────────┘
       │
       │ Composes
       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LayoutView                                     │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Header                                                                  │ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │ ┌─────────────────────────────────────┐ ┌─────────────────────────────┐ │ │
│ │ │      MessageAreaView                │ │     SidebarView             │ │ │
│ │ │                                     │ │                             │ │ │
│ │ │  ┌─────────────────────────────┐   │ │  ┌───────────────────────┐  │ │ │
│ │ │  │ UserMessage                 │   │ │  │ Current Agent         │  │ │ │
│ │ │  │ "What can you do?"          │   │ │  │ agent_snowflake       │  │ │ │
│ │ │  └─────────────────────────────┘   │ │  └───────────────────────┘  │ │ │
│ │ │                                     │ │  ┌───────────────────────┐  │ │ │
│ │ │  ┌─────────────────────────────┐   │ │  │ Current Thread        │  │ │ │
│ │ │  │ AssistantMessage            │   │ │  │ thread-abc123         │  │ │ │
│ │ │  │ "I can help you with..."    │   │ │  └───────────────────────┘  │ │ │
│ │ │  └─────────────────────────────┘   │ │  ┌───────────────────────┐  │ │ │
│ │ │                                     │ │  │ Tokens                │  │ │ │
│ │ │  ┌─────────────────────────────┐   │ │  │ 150 in / 89 out       │  │ │ │
│ │ │  │ ToolCallMessage             │   │ │  └───────────────────────┘  │ │ │
│ │ │  │ sql_db_query(...)           │   │ │                             │ │ │
│ │ │  └─────────────────────────────┘   │ │                             │ │ │
│ │ │                                     │ │                             │ │ │
│ │ └─────────────────────────────────────┘ └─────────────────────────────┘ │ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │ ChatInput                                                               │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ > Type your message here...                                    [↵] │ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │ StatusAreaView                                                          │ │
│ │ ┌─────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ Connected: localhost:2024 │ Agent: agent │ Thread: abc │ 239 tokens│ │ │
│ │ └─────────────────────────────────────────────────────────────────────┘ │ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │ Footer (Key Bindings)                                                   │ │
│ │ F2 Agents │ F3 Threads │ F4 Sidebar │ Ctrl+L Clear │ Ctrl+C Quit       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## TUI Component Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                REPLApp                                      │
│                          (Event Coordinator)                                │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│    Controllers      │  │      AppState       │  │       Views         │
│                     │  │   (Centralized)     │  │                     │
│ MessageController   │  │                     │  │ LayoutView          │
│ SessionController   │  │ - current_agent     │  │ MessageAreaView     │
│ CommandController   │  │ - current_thread    │  │ SidebarView         │
│ InterruptController │  │ - messages[]        │  │ StatusAreaView      │
│                     │  │ - is_loading        │  │                     │
└──────────┬──────────┘  └─────────────────────┘  └─────────────────────┘
           │                                                │
           │                                                │
           ▼                                                ▼
┌─────────────────────────────────────────┐    ┌─────────────────────────┐
│              Services                    │    │        Widgets          │
│                                          │    │                         │
│ ┌──────────────────────────────────────┐ │    │ UserMessage             │
│ │ LangGraphService                     │ │    │ AssistantMessage        │
│ │ - Wraps LangGraphClient              │ │    │ ToolCallMessage         │
│ │ - Caches agents/threads              │ │    │ ChatInput               │
│ │ - Resolves friendly names            │ │    │ Sidebar                 │
│ └──────────────────────────────────────┘ │    │ StatusArea              │
│                                          │    │ LoadingWidget           │
│ ┌──────────────────────────────────────┐ │    │ CommandPalette          │
│ │ StreamService                        │ │    │                         │
│ │ - Wraps StreamHandler                │ │    └─────────────────────────┘
│ │ - UI-friendly processing             │ │
│ └──────────────────────────────────────┘ │
└──────────────────────────────────────────┘
           │
           │
           ▼
┌─────────────────────────────────────────┐
│           Core (Shared)                 │
│                                         │
│ LangGraphClient → langgraph-sdk         │
│ StreamHandler   → ParsedChunk           │
│ SessionState    → Ephemeral state       │
│ Config          → Environment           │
└─────────────────────────────────────────┘
```

## Module Dependency Graph

```
                              ┌─────────────────┐
                              │   __main__.py   │
                              │    (REPLLoop)   │
                              └────────┬────────┘
                                       │
       ┌───────────────┬───────────────┼───────────────┬───────────────┐
       │               │               │               │               │
       ▼               ▼               ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   core/     │ │ streaming/  │ │ commands/   │ │    ui/      │ │   config    │
│  client.py  │ │ handler.py  │ │ registry.py │ │ renderer.py │ │  config.py  │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └─────────────┘ └─────────────┘
       │               │               │
       │               │               │
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ langgraph   │ │   core/     │ │   core/     │
│    sdk      │ │ parsers.py  │ │ session.py  │
└─────────────┘ │ session.py  │ │ client.py   │
               │ types.py    │ │ renderer.py │
               └─────────────┘ └─────────────┘


TUI Additional Dependencies:

                              ┌─────────────────┐
                              │  tui/app.py     │
                              │   (REPLApp)     │
                              └────────┬────────┘
                                       │
       ┌───────────────┬───────────────┼───────────────┬───────────────┐
       │               │               │               │               │
       ▼               ▼               ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ controllers │ │  services   │ │   views     │ │  widgets    │ │   models    │
│             │ │             │ │             │ │             │ │             │
│ message_    │ │ langgraph_  │ │ layout_     │ │ messages.py │ │ app_state   │
│ session_    │ │ stream_     │ │ message_    │ │ input.py    │ │             │
│ command_    │ │             │ │ sidebar_    │ │ sidebar.py  │ │             │
│ interrupt_  │ │             │ │ status_     │ │ status.py   │ │             │
└─────────────┘ └──────┬──────┘ └─────────────┘ └─────────────┘ └─────────────┘
                       │
                       ▼
               ┌─────────────┐
               │    core/    │
               │  (shared)   │
               └─────────────┘
```

## Streaming Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ParsedChunk                                       │
│                        (streaming/types.py)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  chunk_type: ChunkType          ← Discriminator                            │
│  namespace: tuple               ← For parallel agents                       │
│  message_id: str | None                                                     │
│  text_delta: str | None         ← New text content                         │
│  tool_call: ToolCall | None     ← Complete tool invocation                 │
│  interrupt: Interrupt | None    ← HITL signal                              │
│  usage: Usage | None            ← Token counts                             │
│  metadata: dict | None                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            ChunkType                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TEXT_DELTA          │  New text from AI response (streaming)              │
│  TOOL_CALL_COMPLETE  │  Tool call with parsed args                         │
│  TOOL_RESULT         │  Tool execution result                              │
│  INTERRUPT           │  HITL approval needed                               │
│  USAGE               │  Token usage stats                                  │
│  METADATA            │  Run/message metadata                               │
│  ERROR               │  Error event                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│      ToolCall        │  │       Usage          │  │      Interrupt       │
├──────────────────────┤  ├──────────────────────┤  ├──────────────────────┤
│ id: str              │  │ input_tokens: int    │  │ id: str              │
│ name: str            │  │ output_tokens: int   │  │ value: dict          │
│ args: dict           │  │ total_tokens: int    │  │   tool: str          │
│ type: str            │  │                      │  │   args: dict         │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
```

## File Structure

```
apps/repl-client/
├── src/repl_client/
│   ├── __init__.py
│   ├── __main__.py              ← Classic REPL entry (Layer 8)
│   │
│   ├── core/                    ← Foundation (Layers 0-3)
│   │   ├── __init__.py
│   │   ├── logging.py           ← Layer 0: Logging
│   │   ├── client.py            ← Layer 1: LangGraph API
│   │   ├── parsers.py           ← Layer 2: SSE parsing
│   │   ├── session.py           ← Layer 3: State
│   │   └── config.py            ← Configuration
│   │
│   ├── streaming/               ← Stream processing (Layers 4-5)
│   │   ├── __init__.py
│   │   ├── types.py             ← ParsedChunk, ChunkType
│   │   ├── handler.py           ← Layer 4: StreamHandler
│   │   └── hitl.py              ← Layer 5: HITLHandler
│   │
│   ├── commands/                ← Command system (Layer 7)
│   │   ├── __init__.py
│   │   ├── registry.py          ← CommandRegistry
│   │   └── handlers.py          ← Command implementations
│   │
│   ├── ui/                      ← Terminal rendering (Layer 6)
│   │   ├── __init__.py
│   │   ├── renderer.py          ← Rich-based output
│   │   └── content_blocks.py    ← Tool formatters
│   │
│   └── tui/                     ← Textual TUI (Alternative UI)
│       ├── __init__.py
│       ├── __main__.py          ← TUI entry point
│       ├── app.py               ← REPLApp (main app)
│       ├── hitl.py              ← TUI HITL handler
│       │
│       ├── models/
│       │   └── app_state.py     ← Centralized state
│       │
│       ├── services/
│       │   ├── langgraph_service.py
│       │   └── stream_service.py
│       │
│       ├── controllers/
│       │   ├── message_controller.py
│       │   ├── session_controller.py
│       │   ├── command_controller.py
│       │   └── interrupt_controller.py
│       │
│       ├── views/
│       │   ├── layout_view.py
│       │   ├── message_area_view.py
│       │   ├── sidebar_view.py
│       │   └── status_area_view.py
│       │
│       ├── widgets/
│       │   ├── messages.py
│       │   ├── input.py
│       │   ├── sidebar.py
│       │   ├── status.py
│       │   ├── status_area.py
│       │   ├── loading.py
│       │   ├── history.py
│       │   ├── command_palette.py
│       │   └── agent_detail.py
│       │
│       ├── screens/
│       │   ├── welcome.py
│       │   └── agent_config.py
│       │
│       └── styles/
│           ├── theme.tcss
│           ├── layout.tcss
│           ├── components.tcss
│           └── states.tcss
│
├── tests/
├── docs/
├── pyproject.toml
└── Makefile
```
