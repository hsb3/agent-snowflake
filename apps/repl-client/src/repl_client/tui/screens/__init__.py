"""TUI modal screens for REPL client.

Provides ModalScreen subclasses for user interactions that require
focused input before the main app can continue.

Key Classes:
    HITLApprovalScreen: Approval/rejection modal for tool call interrupts.
"""

from repl_client.tui.screens.hitl_approval import HITLApprovalScreen

__all__ = [
    "HITLApprovalScreen",
]
