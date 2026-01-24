---
doc_id: CC-2026-054
document_type: planning
document_title: "Phase 2 Porting Plan: repl_client to repl_client_graph"
document_purpose: "Plan for porting Phase 2 features from traditional to StateGraph REPL"
date: 2026-01-23
status: archived
author: docs-cleanup-agent
version: 1.0
tags: [repl, stategraph, phase2, porting, commands, hitl]
project: repl_client_graph
focus: graph-based-repl
---

# Phase 2 Porting Plan: repl_client → repl_client_graph

## What's Available to Copy

### ✅ Fully Implemented in `repl_client/`

**1. Command Handlers** (`commands/handlers.py` - 336 lines)
- `/agents` - List agents, switch agent, agent name resolution, caching
- `/threads` - List threads, resume thread
- `/new` - Create new thread
- `/info` - Show session summary
- `/clear` - Clear screen
- `/session` - Full state dump

**2. HITL Handler** (`streaming/hitl.py` - 106 lines)
- `HITLHandler` class
- Approval prompts (y/n)
- Tool preview formatting with registry
- Resume command building

**3. Tool Rendering** (`ui/content_blocks.py` - 161 lines)
- `ToolRenderRegistry` - Extensible formatter system
- Builtin formatters (SQL)
- Generic fallback formatter
- `ContentBlockRenderer` class

**Total:** ~600 lines of battle-tested code

## Porting Strategy for StateGraph

### Key Difference: StateGraph vs Traditional Loop

**Traditional REPL (repl_client):**
```python
# Commands directly manipulate session and call client
async def handle_agents(self, args):
    agents = await self.client.list_agents()  # Direct call
    self.session.set_agent(agent_id)          # Direct mutation
    self.renderer.render_table(...)           # Direct render
```

**StateGraph REPL (repl_client_graph):**
```python
# Commands return state updates for graph to propagate
def execute_command_node(state: REPLState) -> REPLState:
    if command == "agents":
        # Prepare async work
        return {**state, "command_result": {"action": "list_agents"}}

    # Graph handles the rest
```

### Approach 1: Inline in execute_command_node ✅ RECOMMENDED

**Pros:**
- Simple - all command logic in one place
- No extra complexity
- Commands are already atomic operations

**Cons:**
- execute_command_node gets larger

**Implementation:**
```python
# graph/nodes/commands.py

async def execute_command_node(state: REPLState) -> REPLState:
    """Execute slash commands - expanded for Phase 2"""

    client = get_client()
    session = get_session()
    renderer = get_renderer()

    user_input = state.get("user_input", "")
    parts = user_input[1:].split()  # Remove /
    command = parts[0] if parts else ""
    args = parts[1:] if len(parts) > 1 else []

    render_queue = []

    # Phase 1 commands
    if command == "help":
        # ... existing code

    elif command == "exit":
        # ... existing code

    # Phase 2 commands - PORT FROM repl_client
    elif command == "agents":
        if args:
            # Switch agent logic
            agent_id = await resolve_agent_id(args[0], client)
            session.set_agent(agent_id)
            render_queue.append({"type": "success", "content": f"Switched to {args[0]}"})
        else:
            # List agents logic
            agents = await client.list_agents()
            # Build table
            render_queue.append({"type": "table", "data": ...})

    elif command == "threads":
        # ... port from repl_client

    # ... etc
```

### Approach 2: Separate Async Command Node

**Pros:**
- Clean separation
- Async commands isolated

**Cons:**
- Adds graph complexity
- Need routing between sync/async commands

**Implementation:**
```python
# Add new node for async commands
graph.add_node("execute_async_command", execute_async_command_node)

# Route based on command type
def route_command(state):
    command = parse_command(state["user_input"])
    if command in ["agents", "threads", "new"]:
        return "async"
    return "sync"

graph.add_conditional_edges(
    "route_input",
    route_command,
    {
        "sync": "execute_command",
        "async": "execute_async_command",
    }
)
```

## Porting Plan - Approach 1

### Step 1: Copy Utilities

Copy these directly (no changes needed):
- `ui/content_blocks.py` → Already copied! ✅
- `streaming/hitl.py` → Need to copy

### Step 2: Enhance execute_command_node

Port command logic from `commands/handlers.py`:

```python
# FROM repl_client/commands/handlers.py (traditional)
async def handle_agents(self, args):
    if args:
        agent_id = await self._resolve_agent_id(args[0])
        self.session.set_agent(agent_id)
        ...
    else:
        agents = await self.client.list_agents()
        ...

# TO repl_client_graph/graph/nodes/commands.py (StateGraph)
async def execute_command_node(state):
    client = get_client()
    session = get_session()

    if command == "agents":
        if args:
            agent_id = await resolve_agent_id(args[0], client)
            session.set_agent(agent_id)  # Still mutates session (OK)
            return {**state, "render_queue": [...]}
        else:
            agents = await client.list_agents()
            return {**state, "render_queue": [...]}
```

### Step 3: Enhance process_stream_node for HITL

Add interrupt detection:

```python
# FROM repl_client/streaming/handler.py
if event_type == "updates":
    if "__interrupt__" in data:
        # Detected interrupt

# TO repl_client_graph/graph/nodes/streaming.py
elif event_type == "updates":
    if isinstance(data, dict) and "__interrupt__" in data:
        pending_interrupt = Interrupt(value=data["__interrupt__"])
        # Return early with interrupt
        return {**state, "pending_interrupt": pending_interrupt, ...}
```

### Step 4: Implement handle_interrupt_node

```python
# FROM repl_client/streaming/hitl.py
def handle_interrupt(self, interrupt, session):
    tool_name = interrupt.value.get("tool", "unknown")
    approved = self._show_approval_prompt(tool_name, ...)
    return {"resume": {"approve": approved}}

# TO repl_client_graph/graph/nodes/hitl.py
async def handle_interrupt_node(state):
    hitl_handler = get_hitl_handler()  # Add to context
    interrupt = state["pending_interrupt"]

    # Show prompt, get approval
    resume_cmd = hitl_handler.handle_interrupt(interrupt, get_session())

    # Resume streaming with approval
    client = get_client()
    resume_chunks = await client.resume_after_interrupt(
        state["current_thread_id"],
        state["current_assistant_id"],
        approved=resume_cmd["resume"]["approve"]
    )

    # Process resumed chunks
    return {**state, "stream_chunks": resume_chunks, "pending_interrupt": None}
```

## Files to Port

### Direct Copy (minimal changes)
1. ✅ `ui/content_blocks.py` - Already copied
2. `streaming/hitl.py` - Copy and update imports

### Adapt for StateGraph
3. `graph/nodes/commands.py` - Expand with Phase 2 command logic
4. `graph/nodes/hitl.py` - Implement interrupt handling
5. `graph/nodes/streaming.py` - Add interrupt detection in updates stream
6. `context.py` - Add HITLHandler and ToolRenderRegistry to context

## Changes Needed

### 1. Commands: Sync → Async
Many commands need async (list_agents, create_thread, etc.)

**Solution:** Make execute_command_node async (already is in stub)

### 2. Interrupt Flow
Traditional REPL detects interrupt in streaming loop.

**StateGraph flow:**
- `process_stream_node` detects interrupt → return with pending_interrupt
- Graph routes to `handle_interrupt_node`
- User approves
- Resume streaming
- Route back to `process_stream_node` with new chunks

### 3. Session Mutation
Commands mutate session directly (session.set_agent, session.set_thread)

**This is OK!** Session is injected via context, mutations are side effects. State dict tracks "what happened" for graph flow.

### 4. Rendering Queue Pattern
All rendering goes through render_queue in state.

**Commands add to queue:**
```python
render_queue.append({"type": "table", "headers": [...], "rows": [...]})
render_queue.append({"type": "success", "content": "Switched agent"})
```

## Estimated Effort

- Copy utilities: 30 min
- Expand execute_command_node: 1-2 hours
- Implement HITL flow: 1-2 hours
- Test integration: 1 hour
- Update docs: 30 min

**Total:** 4-6 hours

## Testing Plan

1. **Unit tests per command:**
   - `/agents` with no args (list)
   - `/agents agent_minimal` (switch)
   - `/threads` list and resume
   - `/new` create thread
   - `/info` display

2. **HITL integration test:**
   - Trigger tool that requires approval
   - Approve and verify execution
   - Reject and verify cancellation

3. **End-to-end flow:**
   - Start REPL
   - Switch agents
   - Create new thread
   - Resume thread
   - Trigger HITL
   - Exit

## Next Steps

1. Copy `streaming/hitl.py` and `ui/content_blocks.py`
2. Update imports for repl_client_graph
3. Expand execute_command_node with Phase 2 commands
4. Implement handle_interrupt_node
5. Add interrupt detection to process_stream_node
6. Update context.py with new dependencies
7. Test each command
8. Update documentation
