---
title: "REPL Data/Control Flow"
created: 2026-01-23
updated: 2026-01-24
status: current
tags: [repl, data-flow, architecture, dag]
type: reference
---

# REPL Data/Control Flow

This document visualizes the data and control flow through the REPL system as a Directed Acyclic Graph.

---

## Key Insights

### DAG Properties
1. **No cycles**: Data flows one direction - User → Input → Process → Render → Display
2. **Clear dependencies**: Each layer only depends on layers below it (lower numbers)
3. **Parallel opportunities**: Parsing and rendering are independent and could be parallelized
4. **State centralization**: SessionState is read by many, written by few

### Critical Paths
1. **Hot path**: User input → Stream → Parse → Render (latency-critical)
2. **HITL path**: Interrupt → Approval → Resume → Stream (user-blocking)
3. **Command path**: Input → Registry → Handler → Render (synchronous)

### Data Transformations
1. SSE string → (event_type, data) tuple
2. Raw dict → ParsedChunk dataclass
3. ParsedChunk → Rendered output
4. Usage metadata → Session token tracking

### Coupling Points
- Stream Handler is deliberately decoupled from Renderer (yields data, doesn't render)
- Command Handlers need Client, Session, and Renderer (tightly coupled)
- Main Loop orchestrates everything (central coordinator)

---

## Overall Architecture Flow

```mermaid
graph TB
    %% Entry point
    User[User Input] --> MainLoop[Main Loop<br/>__main__.py]

    %% Command vs Message routing
    MainLoop --> IsCommand{Starts with<br/>'/' ?}
    IsCommand -->|Yes| CmdRegistry[Command Registry<br/>commands/registry.py]
    IsCommand -->|No| SendMsg[Send Message Flow]

    %% Command flow
    CmdRegistry --> CmdHandlers[Command Handlers<br/>commands/handlers.py]
    CmdHandlers --> Client[LangGraph Client<br/>core/client.py]
    CmdHandlers --> Renderer[Renderer<br/>ui/renderer.py]
    CmdHandlers --> Session[Session State<br/>core/session.py]

    %% Message send flow
    SendMsg --> Client
    Client --> HTTPReq[HTTP POST<br/>/threads/ID/runs/stream]
    HTTPReq --> Server[LangGraph Server<br/>REST API]

    %% Streaming response flow
    Server --> SSEChunks[SSE Event Stream<br/>event: type<br/>data: json]
    SSEChunks --> StreamHandler[Stream Handler<br/>streaming/handler.py]

    %% Parsing flow
    StreamHandler --> Parsers[Parsers<br/>core/parsers.py]
    Parsers --> ParsedChunk[ParsedChunk Objects<br/>TEXT_DELTA<br/>TOOL_CALL<br/>INTERRUPT<br/>USAGE]

    %% Routing parsed chunks
    ParsedChunk --> ChunkRouter{Chunk<br/>Type?}

    %% Text rendering
    ChunkRouter -->|TEXT_DELTA| MsgRenderer[Message Renderer<br/>ui/message.py]
    MsgRenderer --> Display[Terminal Display]

    %% Tool call handling
    ChunkRouter -->|TOOL_CALL| ContentRenderer[Content Block Renderer<br/>ui/content_blocks.py]
    ContentRenderer --> ToolRegistry[Tool Render Registry]
    ToolRegistry --> Display

    %% HITL interrupt handling
    ChunkRouter -->|INTERRUPT| HITLHandler[HITL Handler<br/>streaming/hitl.py]
    HITLHandler --> ApprovalPrompt[Show Approval Prompt]
    ApprovalPrompt --> UserDecision{User<br/>Approves?}
    UserDecision -->|Yes| ResumeApproved[Resume with approve=true]
    UserDecision -->|No| ResumeRejected[Resume with approve=false]
    ResumeApproved --> Client
    ResumeRejected --> Client

    %% Usage tracking
    ChunkRouter -->|USAGE| Session
    Session --> TokenTracking[Token Tracking]

    %% State management
    StreamHandler -.reads.-> Session
    MainLoop -.updates.-> Session

    %% Logging
    Client -.logs to.-> Logger[Client Logger<br/>core/logging.py]
    StreamHandler -.logs to.-> Logger
    CmdHandlers -.logs to.-> Logger

    %% Config
    Config[Config<br/>core/config.py<br/>.env] -.provides.-> Client
    Config -.provides.-> MainLoop

    style User fill:#90EE90
    style Display fill:#87CEEB
    style Server fill:#FFB6C1
    style MainLoop fill:#FFD700
    style ParsedChunk fill:#DDA0DD
```

## Layer Dependencies (Build Order)

```mermaid
graph LR
    L0[Layer 0<br/>Logging] --> L1[Layer 1<br/>HTTP Client]
    L0 --> L2[Layer 2<br/>Parsers]
    L1 --> L4[Layer 4<br/>Stream Handler]
    L2 --> L4
    L3[Layer 3<br/>Session State] --> L4
    L4 --> L6[Layer 6<br/>Renderer]
    L6 --> L8[Layer 8<br/>Main Loop]
    L1 --> L7[Layer 7<br/>Commands]
    L3 --> L7
    L6 --> L7
    L7 --> L8
    L4 --> L5[Layer 5<br/>HITL Handler]
    L6 --> L5
    L5 --> L8

    style L0 fill:#E8E8E8
    style L1 fill:#FFE4B5
    style L2 fill:#FFE4B5
    style L3 fill:#FFE4B5
    style L4 fill:#FFD700
    style L5 fill:#87CEEB
    style L6 fill:#90EE90
    style L7 fill:#90EE90
    style L8 fill:#FF6B6B
```

## Detailed Message Streaming Flow

```mermaid
sequenceDiagram
    participant User
    participant MainLoop
    participant StreamHandler
    participant Client
    participant Server
    participant Parsers
    participant Renderer
    participant Session

    User->>MainLoop: Type message
    MainLoop->>Client: stream_message(thread_id, msg, assistant_id)
    Client->>Server: POST /threads/{id}/runs/stream
    Server-->>Client: SSE chunks (event, data)

    loop For each SSE chunk
        Client-->>StreamHandler: yield (event_type, data)
        StreamHandler->>Parsers: parse_message_chunk(event, data)
        Parsers->>Parsers: extract_text_delta(prev, curr)
        Parsers-->>StreamHandler: ParsedChunk
        StreamHandler->>Session: Update namespace state
        StreamHandler-->>MainLoop: yield ParsedChunk

        alt Chunk type: TEXT_DELTA
            MainLoop->>Renderer: render_text(chunk.text_delta)
            Renderer-->>User: Display text
        else Chunk type: TOOL_CALL
            MainLoop->>Renderer: render_tool_call(chunk.tool_call)
            Renderer-->>User: Display tool preview
        else Chunk type: INTERRUPT
            MainLoop->>HITLHandler: handle_interrupt(chunk.interrupt)
            HITLHandler->>Renderer: show_approval_prompt()
            Renderer-->>User: Show approval UI
            User->>HITLHandler: y/n decision
            HITLHandler->>Client: resume_after_interrupt(approved)
            Client->>Server: POST with command.resume
        else Chunk type: USAGE
            MainLoop->>Session: track_tokens(usage)
        end
    end

    MainLoop-->>User: Stream complete
```

## Data Structures Flow

```mermaid
graph TB
    %% Raw input
    SSE[SSE Event<br/>event: messages/partial<br/>data: json] --> Parser

    %% Parsing stage
    Parser[parse_message_chunk] --> Extract[extract_text_delta<br/>extract_content_blocks<br/>detect_tool_call]

    %% Structured output
    Extract --> ParsedChunk[ParsedChunk<br/>dataclass]

    %% ParsedChunk fields
    ParsedChunk --> ChunkType[chunk_type: ChunkType enum]
    ParsedChunk --> Namespace[namespace: tuple]
    ParsedChunk --> TextDelta[text_delta: str]
    ParsedChunk --> ToolCall[tool_call: ToolCall]
    ParsedChunk --> Interrupt[interrupt: Interrupt]
    ParsedChunk --> Usage[usage: Usage]

    %% ContentBlock detail
    TextDelta --> ContentBlock[ContentBlock<br/>dataclass]
    ContentBlock --> CBType[type: str]
    ContentBlock --> CBText[text: str]
    ContentBlock --> CBTool[tool_name/args/id]

    %% ToolCall detail
    ToolCall --> TCFields[id: str<br/>name: str<br/>args: dict]

    %% Interrupt detail
    Interrupt --> IntFields[tool_id: str<br/>tool_name: str<br/>tool_args: dict]

    %% Usage detail
    Usage --> UsageFields[input_tokens: int<br/>output_tokens: int<br/>total_tokens: int]

    style SSE fill:#FFB6C1
    style ParsedChunk fill:#FFD700
    style ChunkType fill:#90EE90
    style ContentBlock fill:#87CEEB
```

## Command Flow vs Message Flow

```mermaid
graph LR
    Input[User Input] --> Router{Type?}

    %% Command path
    Router -->|/command| CmdParse[Parse command<br/>split args]
    CmdParse --> CmdReg[Command Registry<br/>lookup handler]
    CmdReg --> CmdExec[Execute Handler]

    CmdExec --> CmdType{Command<br/>Type?}
    CmdType -->|/help| ShowHelp[Render help text]
    CmdType -->|/exit| ExitLoop[Return False<br/>exit REPL]
    CmdType -->|/agents| ListAgents[Call client.list_agents<br/>Render table]
    CmdType -->|/threads| ListThreads[Call client.list_threads<br/>Render table]
    CmdType -->|/new| CreateThread[Call client.create_thread<br/>Update session]
    CmdType -->|/info| ShowInfo[Get session state<br/>Render summary]

    %% Message path
    Router -->|message| ValidateMsg[Validate non-empty]
    ValidateMsg --> CheckSession{Has thread<br/>and agent?}
    CheckSession -->|No| CreateAuto[Auto-create thread]
    CheckSession -->|Yes| StreamMsg[Stream message]
    CreateAuto --> StreamMsg
    StreamMsg --> ProcessStream[Process SSE stream<br/>yield ParsedChunks]
    ProcessStream --> RenderChunks[Render each chunk<br/>in real-time]

    style Input fill:#90EE90
    style Router fill:#FFD700
    style CmdReg fill:#87CEEB
    style StreamMsg fill:#FFB6C1
```

## State Management

```mermaid
graph TB
    Session[SessionState] --> ThreadID[current_thread_id: str]
    Session --> AgentID[current_assistant_id: str]
    Session --> RunID[current_run_id: str]
    Session --> NSState[namespace_state: dict]
    Session --> Tokens[session_tokens: dict]
    Session --> StartTime[session_start_time: float]

    %% Who updates what
    MainLoop[Main Loop] -.creates thread.-> ThreadID
    CmdHandlers[Command Handlers] -.switches agent.-> AgentID
    CmdHandlers -.switches thread.-> ThreadID
    StreamHandler[Stream Handler] -.sets run.-> RunID
    StreamHandler -.tracks namespace.-> NSState
    StreamHandler -.adds usage.-> Tokens

    %% Who reads what
    StreamHandler -.reads.-> NSState
    Renderer -.reads for prompt.-> AgentID
    CmdHandlers -.reads for /info.-> Session
    HITLHandler -.reads for resume.-> RunID

    style Session fill:#FFD700
    style MainLoop fill:#87CEEB
    style CmdHandlers fill:#90EE90
    style StreamHandler fill:#FFB6C1
```

## Error Handling Flow

```mermaid
graph TB
    Error[Error Occurs] --> Source{Error<br/>Source?}

    Source -->|Connection| ConnError[Connection Failed]
    ConnError --> Retry{Retry?}
    Retry -->|Yes| BackOff[Exponential backoff]
    Retry -->|No| ShowError[Render error message]
    BackOff --> ReConnect[Attempt reconnect]

    Source -->|Parse| ParseError[Malformed SSE/JSON]
    ParseError --> LogWarn[Log warning]
    LogWarn --> SkipChunk[Skip chunk<br/>continue stream]

    Source -->|Server| ServerError[HTTP 4xx/5xx]
    ServerError --> CheckCode{Status<br/>Code?}
    CheckCode -->|404| NotFound[Thread/Agent not found<br/>Create new?]
    CheckCode -->|429| RateLimit[Rate limited<br/>Wait and retry]
    CheckCode -->|500| ServerDown[Server error<br/>Show message]

    Source -->|Stream| StreamError[Stream interrupted]
    StreamError --> Partial[Partial response received?]
    Partial -->|Yes| ShowPartial[Display what we got]
    Partial -->|No| ShowFailed[Show failed message]

    ShowError --> UserDecision{User<br/>Action?}
    UserDecision -->|Retry| ReConnect
    UserDecision -->|Exit| Quit[Exit REPL]
    UserDecision -->|New Thread| CreateNew[new command]

    style Error fill:#FF6B6B
    style ShowError fill:#FFB6C1
```

