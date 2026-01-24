#!/usr/bin/env python3
"""Demo script for HITL Handler (Layer 5)

Shows how the HITLHandler integrates with the Renderer and ToolRenderRegistry.
"""

from repl_client.streaming.hitl import HITLHandler
from repl_client.streaming.types import Interrupt
from repl_client.ui.renderer import Renderer
from repl_client.ui.content_blocks import ToolRenderRegistry
from repl_client.core.session import SessionState


def demo_basic_approval():
    """Demo basic approval flow"""
    print("\n=== Demo 1: Basic Approval Flow ===\n")

    # Setup
    renderer = Renderer()
    handler = HITLHandler(renderer=renderer)
    session = SessionState()

    # Create interrupt for SQL query
    interrupt = Interrupt(
        id="int_001",
        value={
            "tool": "sql_db_query",
            "args": {
                "query": "SELECT * FROM users WHERE active = true LIMIT 10"
            }
        }
    )

    print("Simulating interrupt for SQL query tool...")
    print("(In real use, user would type 'y' or 'n')\n")

    # In real use, this would prompt the user
    # For demo, we'll show what would be displayed
    renderer.render_panel(
        content=handler._format_tool_preview("sql_db_query", interrupt.value["args"]),
        title=f"Tool Approval Required: sql_db_query",
        style="yellow"
    )

    print("\nCommand that would be sent if approved:")
    print(handler._build_resume_command(approved=True, interrupt=interrupt))

    print("\nCommand that would be sent if rejected:")
    print(handler._build_resume_command(approved=False, interrupt=interrupt))


def demo_custom_formatter():
    """Demo custom tool formatter"""
    print("\n\n=== Demo 2: Custom Tool Formatter ===\n")

    # Setup with custom formatter
    renderer = Renderer()
    registry = ToolRenderRegistry()

    # Register custom formatter for hypothetical tool
    def format_email_tool(args: dict) -> str:
        to = args.get("to", "unknown")
        subject = args.get("subject", "No subject")
        body = args.get("body", "")
        return f"To: {to}\nSubject: {subject}\n\n{body[:100]}..."

    registry.register("send_email", format_email_tool)

    handler = HITLHandler(renderer=renderer, tool_registry=registry)

    # Create interrupt for email tool
    interrupt = Interrupt(
        id="int_002",
        value={
            "tool": "send_email",
            "args": {
                "to": "user@example.com",
                "subject": "Important Update",
                "body": "This is a test email with important information that the user should review before sending."
            }
        }
    )

    print("Custom formatter for email tool:")
    renderer.render_panel(
        content=handler._format_tool_preview("send_email", interrupt.value["args"]),
        title="Custom Tool Format",
        style="yellow"
    )


def demo_generic_fallback():
    """Demo generic fallback for unknown tools"""
    print("\n\n=== Demo 3: Generic Fallback ===\n")

    renderer = Renderer()
    handler = HITLHandler(renderer=renderer)

    # Unknown tool
    interrupt = Interrupt(
        id="int_003",
        value={
            "tool": "custom_analytics_tool",
            "args": {
                "metric": "user_engagement",
                "period": "last_30_days",
                "threshold": 0.75
            }
        }
    )

    print("Unknown tool uses generic JSON format:")
    renderer.render_panel(
        content=handler._format_tool_preview(
            "custom_analytics_tool",
            interrupt.value["args"]
        ),
        title="Generic Tool Format",
        style="yellow"
    )


def main():
    """Run all demos"""
    print("=" * 60)
    print("HITL Handler Demo - Layer 5 (Phase 2)")
    print("=" * 60)

    demo_basic_approval()
    demo_custom_formatter()
    demo_generic_fallback()

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
