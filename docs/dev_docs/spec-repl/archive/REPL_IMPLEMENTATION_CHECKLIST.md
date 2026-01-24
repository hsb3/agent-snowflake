# REPL Client Implementation Checklist

## Phase 1: Core REPL (MVP)

### Setup
- [ ] Create `src/agent_snowflake/repl/` directory
- [ ] Create `__init__.py` with module exports
- [ ] Create `__main__.py` with entry point
- [ ] Install dependencies: `uv add rich prompt-toolkit`

### Configuration Module (`config.py`)
- [ ] Create `Config` dataclass
- [ ] Implement `from_environment()` class method
- [ ] Implement `from_cli_args()` class method
- [ ] Add URL validation function
- [ ] Add environment variable reading with fallbacks
- [ ] Write tests: `tests/repl/test_config.py`

### Connection Module (`client.py`)
- [ ] Create `ConnectionManager` class
- [ ] Implement `__init__()` with langgraph_sdk client
- [ ] Implement `validate_connection()` method
- [ ] Implement `list_assistants()` method
- [ ] Implement `create_thread()` method
- [ ] Implement `stream_message()` method
- [ ] Add error handling for connection failures
- [ ] Add retry logic for transient failures (optional)
- [ ] Write tests: `tests/repl/test_client.py`

### Session State Module (`session.py`)
- [ ] Create `SessionState` dataclass
- [ ] Implement `add_message()` method
- [ ] Implement `reset_thread()` method
- [ ] Implement `get_recent_history()` method
- [ ] Add max_history enforcement
- [ ] Write tests: `tests/repl/test_session.py`

### Output Module (`render.py`)
- [ ] Create `OutputRenderer` class
- [ ] Implement basic `user_message()` method
- [ ] Implement basic `agent_message()` method
- [ ] Implement `system_message()` method
- [ ] Implement `error()` method
- [ ] Implement `separator()` method
- [ ] Add graceful fallback for no-Rich environments
- [ ] Write tests: `tests/repl/test_render.py`

### Stream Handler Module (`stream.py`)
- [ ] Create `StreamHandler` class
- [ ] Implement `process_stream()` method
- [ ] Implement `_extract_content()` helper
- [ ] Handle `messages/partial` events
- [ ] Handle `messages/complete` events
- [ ] Handle `error` events
- [ ] Add timeout handling
- [ ] Add KeyboardInterrupt handling
- [ ] Write tests: `tests/repl/test_stream.py`

### Command Module (`commands.py`)
- [ ] Create `CommandRouter` class
- [ ] Implement command registry
- [ ] Implement `execute()` method
- [ ] Implement `/help` command
- [ ] Implement `/exit` and `/quit` commands
- [ ] Implement `/clear` command
- [ ] Add error handling for unknown commands
- [ ] Write tests: `tests/repl/test_commands.py`

### Main REPL Loop (`__main__.py`)
- [ ] Create `main()` function
- [ ] Parse CLI arguments with argparse
- [ ] Load configuration
- [ ] Initialize ConnectionManager
- [ ] Validate connection and display status
- [ ] List and select assistant
- [ ] Create initial thread
- [ ] Implement input loop (basic, single-line)
- [ ] Route input to command or message handler
- [ ] Handle Ctrl+C gracefully
- [ ] Handle Ctrl+D (EOF) gracefully
- [ ] Add startup banner/welcome message
- [ ] Add exit message

### Integration Testing
- [ ] Test full flow: connect → select → chat → exit
- [ ] Test with all three agents (agent, agent_enhanced, agent_minimal)
- [ ] Test error cases: server down, invalid assistant, timeout
- [ ] Test command execution: /help, /clear, /exit
- [ ] Test streaming with various response sizes

---

## Phase 2: Enhanced UX

### Rich Integration (`render.py` enhancements)
- [ ] Add `rich.console.Console` integration
- [ ] Add `rich.spinner.Spinner` for "thinking" indicator
- [ ] Add `rich.panel.Panel` for message framing
- [ ] Add `rich.markdown.Markdown` for message rendering
- [ ] Add syntax highlighting for code blocks
- [ ] Add live rendering during streaming
- [ ] Test color output in various terminals

### prompt-toolkit Integration (`input.py`)
- [ ] Create `InputHandler` class
- [ ] Add `prompt_toolkit.PromptSession`
- [ ] Add `InMemoryHistory` for input history
- [ ] Add `CommandCompleter` for tab completion
- [ ] Implement command name completion
- [ ] Test up/down arrow navigation
- [ ] Test tab completion

### Additional Commands (`commands.py`)
- [ ] Implement `/history` command
  - [ ] Display last N messages
  - [ ] Format with timestamps
  - [ ] Show user vs agent distinction
- [ ] Implement `/info` command
  - [ ] Show server URL
  - [ ] Show current assistant
  - [ ] Show thread ID
  - [ ] Show message count
  - [ ] Mask API key if present
- [ ] Implement `/assistant` command
  - [ ] List available assistants
  - [ ] Switch to different assistant
  - [ ] Create new thread on switch
  - [ ] Show current assistant if no arg

### CLI Arguments (`__main__.py`)
- [ ] Add `--url` argument
- [ ] Add `--assistant` argument
- [ ] Add `--thread-id` argument
- [ ] Add `--no-color` argument
- [ ] Add `--help` output
- [ ] Add `--version` argument (show version)
- [ ] Test all argument combinations

### Error Handling Improvements
- [ ] Add connection retry logic with backoff
- [ ] Add detailed error messages for common failures
- [ ] Add troubleshooting hints in error output
- [ ] Handle malformed stream responses
- [ ] Handle partial message rendering on error
- [ ] Add debug logging (optional `--debug` flag)

### User Experience Polish
- [ ] Add startup time optimization
- [ ] Add loading indicators for slow operations
- [ ] Add message timestamps (toggleable)
- [ ] Add copy/paste support (test in terminal)
- [ ] Add clear screen helper (Ctrl+L)
- [ ] Test on macOS, Linux, Windows terminals
- [ ] Add demo GIF to documentation

---

## Phase 3: Optional Enhancements

### Multi-line Input
- [ ] Add multi-line mode detection (empty line submits)
- [ ] Add `/multi` command to toggle mode
- [ ] Update InputHandler for multi-line support
- [ ] Add visual indicator for multi-line mode
- [ ] Test with complex queries

### Thread Management
- [ ] Implement `/threads` command to list threads
- [ ] Implement `/resume <thread_id>` command
- [ ] Save last thread_id to temp file
- [ ] Add `--resume-last` flag
- [ ] Test thread persistence across sessions

### Configuration File
- [ ] Define `.repl.yaml` schema
- [ ] Implement YAML config loading
- [ ] Merge config: file < env < CLI args
- [ ] Add `/config` command to show current config
- [ ] Document configuration options

### Streaming Mode Selection
- [ ] Add `--stream-mode` CLI argument
- [ ] Support "messages", "values", "events" modes
- [ ] Add `/mode` command to switch dynamically
- [ ] Adjust output rendering per mode
- [ ] Test each mode with different agents

### Conversation Export
- [ ] Implement `/export <filename>` command
- [ ] Support JSON format export
- [ ] Support Markdown format export
- [ ] Include metadata (timestamps, assistant, thread_id)
- [ ] Test with long conversations

### Advanced Stream Handling
- [ ] Add support for tool call events
- [ ] Display intermediate thinking steps
- [ ] Add progress indicator for multi-step operations
- [ ] Handle stream interruption/cancellation
- [ ] Test with slow/fast streaming

---

## Documentation

### User Documentation
- [ ] Add "REPL Usage" section to main README.md
- [ ] Create quickstart guide (30-second setup)
- [ ] Document all commands with examples
- [ ] Add troubleshooting section
- [ ] Add FAQ section
- [ ] Create example session transcript
- [ ] Add demo video or GIF

### Developer Documentation
- [ ] Document architecture in main README
- [ ] Add inline docstrings to all classes/methods
- [ ] Create CONTRIBUTING.md for REPL contributions
- [ ] Document extension points (custom commands)
- [ ] Add API reference for public interfaces

---

## Testing

### Unit Tests
- [ ] `tests/repl/test_config.py` - Configuration loading
- [ ] `tests/repl/test_client.py` - Connection management (mocked)
- [ ] `tests/repl/test_session.py` - State management
- [ ] `tests/repl/test_commands.py` - Command execution
- [ ] `tests/repl/test_stream.py` - Stream parsing
- [ ] `tests/repl/test_render.py` - Output formatting
- [ ] Achieve >80% code coverage

### Integration Tests
- [ ] `tests/repl/test_integration.py` - Full REPL flow
- [ ] Mock LangGraph server responses
- [ ] Test startup → chat → exit flow
- [ ] Test error recovery
- [ ] Test command sequences

### Manual Testing
- [ ] Test against live dev server
- [ ] Test with Chinook database agent
- [ ] Test with all three agent variants
- [ ] Test streaming with long responses
- [ ] Test streaming with rapid responses
- [ ] Test interruption (Ctrl+C) during streaming
- [ ] Test on macOS
- [ ] Test on Linux
- [ ] Test on Windows (if applicable)
- [ ] Test with different terminal emulators

---

## Deployment

### Package Setup
- [ ] Add REPL dependencies to `pyproject.toml`
  ```toml
  dependencies = [
      # ... existing ...
      "rich>=13.7.0",
      "prompt-toolkit>=3.0.43",
  ]
  ```
- [ ] Add console script entry point (optional)
  ```toml
  [project.scripts]
  snowflake-repl = "agent_snowflake.repl.__main__:main"
  ```
- [ ] Update README with installation instructions

### CI/CD
- [ ] Add REPL tests to CI pipeline
- [ ] Add linting for REPL code
- [ ] Add type checking for REPL code (ty)
- [ ] Test installation in fresh environment

### Release
- [ ] Tag release: v1.0.0-repl
- [ ] Update CHANGELOG.md
- [ ] Create GitHub release notes
- [ ] Share demo/announcement

---

## Quality Assurance Checklist

### Code Quality
- [ ] All functions have docstrings
- [ ] All complex logic has inline comments
- [ ] No hardcoded values (use config)
- [ ] No print statements (use renderer)
- [ ] No bare except clauses
- [ ] Type hints on all public methods
- [ ] Passes `ruff check`
- [ ] Passes `ty check`

### User Experience
- [ ] Clear error messages with actionable advice
- [ ] Fast startup (<1 second)
- [ ] Responsive streaming (updates feel real-time)
- [ ] Keyboard shortcuts work (Ctrl+C, Ctrl+D, arrows)
- [ ] No unexpected crashes
- [ ] Graceful degradation (plain output if Rich unavailable)

### Documentation
- [ ] All commands documented
- [ ] All CLI flags documented
- [ ] All environment variables documented
- [ ] Quickstart guide complete
- [ ] Troubleshooting guide complete
- [ ] Code examples provided

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing complete
- [ ] Edge cases handled
- [ ] Error paths tested

---

## Post-Launch

### User Feedback
- [ ] Collect user feedback on UX
- [ ] Track common issues/questions
- [ ] Identify most-used features
- [ ] Identify least-used features

### Maintenance
- [ ] Monitor for langgraph-sdk updates
- [ ] Update dependencies regularly
- [ ] Address reported bugs
- [ ] Add requested features (if aligned with vision)

### Future Enhancements (v2.0)
- [ ] TUI mode with split panes (textual)
- [ ] Real-time state visualization
- [ ] Interactive graph execution control
- [ ] LangSmith integration for tracing
- [ ] Multi-agent support (switch between agents)

---

## Success Metrics

### MVP (Phase 1)
- ✓ Can connect to local server
- ✓ Can chat with agent
- ✓ Streaming works
- ✓ Basic commands work
- ✓ Zero crashes in happy path

### v1.0 (Phase 2)
- ✓ 90% positive user feedback
- ✓ Used by at least 3 team members
- ✓ All core commands tested
- ✓ Documentation complete
- ✓ <5 bugs reported in first month

### v1.1+ (Phase 3)
- ✓ Power users report productivity gains
- ✓ Feature requests align with roadmap
- ✓ Community contributions (if open source)
- ✓ Integration with other tools (LangSmith, etc.)

---

## Timeline Estimates

### Phase 1: Core REPL
**Estimate**: 2-3 days
- Day 1: Setup, config, connection, session modules
- Day 2: Render, stream, commands modules
- Day 3: Main loop, basic testing, polish

### Phase 2: Enhanced UX
**Estimate**: 2-3 days
- Day 1: Rich integration, prompt-toolkit
- Day 2: Additional commands, CLI args
- Day 3: Error handling, testing, documentation

### Phase 3: Optional Enhancements
**Estimate**: 3-5 days (pick features based on priority)
- Multi-line input: 0.5 days
- Thread management: 1 day
- Config file: 0.5 days
- Stream modes: 1 day
- Export: 0.5 days
- Advanced features: 1-2 days

**Total**: 7-11 days for full v1.1 implementation

---

## Risk Mitigation

### Technical Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| langgraph-sdk API changes | High | Pin version, monitor releases |
| Streaming performance issues | Medium | Buffer chunks, optimize rendering |
| Terminal compatibility | Medium | Test on multiple terminals, graceful fallback |
| Rich/prompt-toolkit conflicts | Low | Test integration early |

### User Adoption Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Users prefer LangGraph Studio | High | Position as complementary tool |
| Too complex to configure | Medium | Minimize required config |
| Not enough features | Medium | Prioritize most-requested features |
| Documentation insufficient | Medium | Write docs early, get feedback |

---

## Decision Log

### Decision 1: Sync vs Async Client
**Date**: 2026-01-23
**Decision**: Use synchronous client (`get_sync_client`)
**Rationale**: Simpler REPL loop, easier error handling, streaming works with sync iterator
**Alternatives Considered**: Async client with asyncio.run()

### Decision 2: Rich vs Textual
**Date**: 2026-01-23
**Decision**: Use Rich for v1, defer Textual to v2
**Rationale**: Rich is simpler for basic formatting. Textual is better for full TUI but overkill for MVP
**Alternatives Considered**: Textual (too complex), plain text (too basic)

### Decision 3: prompt-toolkit vs readline
**Date**: 2026-01-23
**Decision**: Use prompt-toolkit
**Rationale**: Better features (completion, history, key bindings). Standard library readline is too basic
**Alternatives Considered**: readline (limited), built-in input() (no history)

### Decision 4: Stream Mode Default
**Date**: 2026-01-23
**Decision**: Default to "messages" stream mode
**Rationale**: Cleanest output for end users. Power users can change with flag
**Alternatives Considered**: "values" (too verbose), "events" (for debugging only)

### Decision 5: Thread Creation
**Date**: 2026-01-23
**Decision**: Auto-create thread on first message
**Rationale**: Simplest UX. Thread ID displayed after creation
**Alternatives Considered**: Require /new command (extra step), prompt on startup (annoying)

---

## Notes

- Keep implementation simple and focused
- Prioritize working code over perfect code
- Get feedback early and iterate
- Document as you go, not after
- Test in real usage scenarios
- Make it easy to extend (plugins, custom commands)
