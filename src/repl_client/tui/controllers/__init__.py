"""Controllers for TUI application.

Controllers contain business logic and orchestrate between services and views.
They are the middle layer between app (UI coordination) and services (data/streaming).

Architecture:
- MessageController: Handle message sending and streaming
- SessionController: Handle agent/thread switching
- CommandController: Handle slash command execution
- InterruptController: Handle HITL interrupts

Design pattern: Controller → Services → HTTP/Parsing
                Controller → Views (widget mounting)
                App → Controller (event routing)

Like a webapp MVC:
- Model: Services + SessionState
- View: Widgets
- Controller: These classes
"""

from repl_client.tui.controllers.command_controller import CommandController
from repl_client.tui.controllers.interrupt_controller import InterruptController
from repl_client.tui.controllers.message_controller import MessageController
from repl_client.tui.controllers.session_controller import SessionController

__all__ = [
    "MessageController",
    "SessionController",
    "CommandController",
    "InterruptController",
]
