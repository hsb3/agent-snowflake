#!/usr/bin/env python3
"""Demo script to showcase Layer 6 Renderer capabilities"""

from repl_client.ui import (
    Renderer,
    MessageRenderer,
    ContentBlockRenderer,
    ToolRenderRegistry,
    ContentBlock,
    ToolCall,
)


def demo_base_renderer():
    """Demo base renderer capabilities"""
    print("\n" + "=" * 80)
    print("DEMO: Base Renderer")
    print("=" * 80)

    renderer = Renderer()

    # Text rendering
    renderer.render_text("This is cyan text (default)")
    renderer.render_text("This is green text", style="green")
    renderer.render_text("This is yellow text", style="yellow")

    # Markdown rendering
    renderer.render_markdown("""
# Markdown Support

This renderer supports **bold**, *italic*, and `inline code`.

## Lists
- Item 1
- Item 2
- Item 3

## Code blocks
```python
def hello():
    print("world")
```
""")

    # Code with syntax highlighting
    renderer.render_code("SELECT * FROM users WHERE id = 1", "sql")

    # Panel
    renderer.render_panel("This is panel content", title="Panel Title", style="blue")

    # Table
    renderer.render_table(
        headers=["Name", "Age", "City"],
        rows=[
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"],
        ]
    )

    # Error and Success
    renderer.render_error("This is an error message")
    renderer.render_success("This is a success message")


def demo_message_renderer():
    """Demo message renderer capabilities"""
    print("\n" + "=" * 80)
    print("DEMO: Message Renderer")
    print("=" * 80)

    renderer = Renderer()
    msg_renderer = MessageRenderer(renderer)

    # User message
    msg_renderer.render_user_message("What tables are in the database?")

    # AI response with markdown
    msg_renderer.render_ai_text("""
I can help you with that. Let me query the database to find all tables.

The database contains the following tables:
- **customers**
- **orders**
- **products**
""")

    # Tool result
    msg_renderer.render_tool_result(
        tool_name="sql_db_query",
        result="Found 3 tables: customers, orders, products",
        status="success"
    )


def demo_content_block_renderer():
    """Demo content block renderer with tool registry"""
    print("\n" + "=" * 80)
    print("DEMO: Content Block Renderer + Tool Registry")
    print("=" * 80)

    renderer = Renderer()
    registry = ToolRenderRegistry()

    # Register custom formatter
    def format_weather(args: dict) -> str:
        city = args.get("city", "Unknown")
        units = args.get("units", "fahrenheit")
        return f"Getting weather for {city} in {units}"

    registry.register("get_weather", format_weather)

    cb_renderer = ContentBlockRenderer(renderer, registry)

    # Text block
    block = ContentBlock(type="text", index=0, text="Let me check the database...")
    cb_renderer.render_content_block(block)

    # Tool use block (SQL - builtin formatter)
    tool_block = ContentBlock(
        type="tool_use",
        index=1,
        tool_id="call_123",
        tool_name="sql_db_query",
        tool_input={"query": "SELECT COUNT(*) FROM customers"}
    )
    cb_renderer.render_content_block(tool_block)

    # Tool call (custom formatter)
    tool_call = ToolCall(
        id="call_456",
        name="get_weather",
        args={"city": "San Francisco", "units": "celsius"}
    )
    cb_renderer.render_tool_call(tool_call)

    # Tool result block
    result_block = ContentBlock(
        type="tool_result",
        index=2,
        tool_id="call_123",
        text="Count: 150 customers"
    )
    cb_renderer.render_content_block(result_block)


def main():
    """Run all demos"""
    demo_base_renderer()
    demo_message_renderer()
    demo_content_block_renderer()

    print("\n" + "=" * 80)
    print("All demos complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
