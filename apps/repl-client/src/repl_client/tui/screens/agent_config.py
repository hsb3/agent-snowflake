"""Agent configuration screen for viewing and editing agent context schema.

Provides a modal screen with three tabs:
1. Select Agent - choose which agent's config to view
2. Schema Viewer - displays the context_schema for the selected agent
3. Create Assistant - form for creating new assistant with custom context values (TODO)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Label,
    Static,
    TabbedContent,
    TabPane,
)

from repl_client.core.logging import get_logger
from repl_client.tui.widgets.agent_detail import AgentSelector

if TYPE_CHECKING:
    from repl_client.tui.services import LangGraphService

logger = get_logger("tui.screens.agent_config")


def _truncate_uuid(uuid: str, length: int = 8) -> str:
    """Truncate UUID for display, keeping first N characters."""
    if len(uuid) <= length:
        return uuid
    return f"{uuid[:length]}..."


class SchemaFieldWidget(Static):
    """Widget displaying a single schema field with its properties.

    Styling is handled by the main stylesheet (styles/index.tcss).
    """

    def __init__(
        self,
        field_name: str,
        field_type: str,
        default_value: str,
        description: str,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.field_name = field_name
        self.field_type = field_type
        self.default_value = default_value
        self.description = description

    def compose(self) -> ComposeResult:
        """Compose the field widget."""
        with Vertical():
            with Horizontal():
                yield Label(self.field_name, classes="field-name")
                yield Label(f"({self.field_type})", classes="field-type")
                if self.default_value:
                    yield Label(f"= {self.default_value}", classes="field-default")
            if self.description:
                yield Label(self.description, classes="field-description")


class SchemaViewer(VerticalScroll):
    """Scrollable viewer for displaying context_schema fields.

    Styling is handled by the main stylesheet (styles/index.tcss).
    """

    def __init__(self, schemas: dict | None = None, **kwargs):
        super().__init__(**kwargs)
        self.schemas = schemas
        logger.debug(f"SchemaViewer initialized with schemas: {schemas is not None}")
        if schemas:
            logger.debug(f"Schema keys: {list(schemas.keys())}")

    def compose(self) -> ComposeResult:
        """Compose the schema viewer."""
        logger.debug(f"SchemaViewer.compose() called, schemas={self.schemas is not None}")
        yield from self._build_schema_content()

    def _build_schema_content(self) -> ComposeResult:
        """Build schema content widgets."""
        if not self.schemas:
            logger.warning("No schema data available for viewer")
            yield Label("Select an agent to view its schema", classes="schema-empty")
            return

        graph_id = self.schemas.get("graph_id", "unknown")
        logger.debug(f"Displaying schema for graph_id: {graph_id}")
        yield Label(f"Graph: {graph_id}", classes="schema-graph-id")

        context_schema = self.schemas.get("context_schema", {})
        properties = context_schema.get("properties", {})

        logger.debug(f"Context schema has {len(properties)} properties")

        if not properties:
            logger.warning("No context schema properties defined")
            yield Label("No context schema defined for this agent", classes="schema-empty")
            return

        yield Label(f"Context Schema ({len(properties)} fields)", classes="schema-header")

        # Sort properties alphabetically for consistent display
        for field_name in sorted(properties.keys()):
            field_def = properties[field_name]
            field_type = field_def.get("type", "unknown")
            default_value = self._format_default(field_def.get("default"))
            description = field_def.get("description", "")

            logger.debug(f"Adding field: {field_name} ({field_type})")
            yield SchemaFieldWidget(
                field_name=field_name,
                field_type=field_type,
                default_value=default_value,
                description=description,
            )

    def update_schemas(self, schemas: dict | None) -> None:
        """Update the displayed schemas dynamically."""
        logger.debug(f"SchemaViewer.update_schemas called, schemas={schemas is not None}")
        self.schemas = schemas
        self.remove_children()
        for widget in self._build_schema_content():
            self.mount(widget)

    def _format_default(self, value) -> str:
        """Format default value for display."""
        if value is None:
            return ""
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, str):
            # Truncate long strings
            if len(value) > 50:
                return f'"{value[:47]}..."'
            return f'"{value}"'
        return str(value)


class AgentConfigScreen(ModalScreen[dict | None]):
    """Modal screen for viewing agent configuration and context schema.

    Displays a tabbed interface with:
    - Tab 1: Select Agent - list of agents with keyboard navigation
    - Tab 2: Schema Viewer - shows context_schema fields with descriptions
    - Tab 3: Create Assistant - form for creating new assistant (placeholder)

    Flow:
    1. Screen opens with agent list (from POST /assistants/search)
    2. User navigates with Up/Down, selects with Enter
    3. On selection: fetch schemas (GET /assistants/{id}/schemas)
    4. Switch to Schema Viewer tab with the detailed schema

    Styling is handled by the main stylesheet (styles/index.tcss).

    Returns:
        dict with action and data if user performs an action, None if cancelled
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        agents: list[dict],
        current_agent_id: str,
        langgraph_service: LangGraphService,
    ):
        """Initialize the config screen.

        Args:
            agents: List of agent dictionaries from /assistants/search
            current_agent_id: Currently selected agent's assistant_id
            langgraph_service: Service for fetching schemas
        """
        super().__init__()
        self.agents = agents
        self.current_agent_id = current_agent_id
        self.langgraph_service = langgraph_service
        self.selected_agent: dict | None = None
        self.schemas: dict | None = None

        logger.info(
            f"AgentConfigScreen initialized with {len(agents)} agents, "
            f"current_agent_id={current_agent_id}"
        )

    def compose(self) -> ComposeResult:
        """Compose the config screen."""
        logger.debug("Composing AgentConfigScreen")

        with Container():
            yield Label("Agent Configuration", classes="config-title")

            with TabbedContent():
                with TabPane("Select Agent", id="tab-select"):
                    logger.debug("Creating AgentSelector tab")
                    yield AgentSelector(self.agents, self.current_agent_id)

                with TabPane("Schema Viewer", id="tab-schema"):
                    logger.debug("Creating SchemaViewer tab")
                    yield SchemaViewer()

                with TabPane("Create Assistant", id="tab-create"):
                    yield Label(
                        "Create new assistant with custom context values\n\n"
                        "(Coming soon - will allow creating new assistants\n"
                        "based on this agent with modified context values)",
                        classes="placeholder-message",
                    )

            with Horizontal(classes="button-bar"):
                yield Button("Close", variant="default", id="btn-close")

        logger.debug("AgentConfigScreen compose complete")

    def on_mount(self) -> None:
        """Focus on mount."""
        logger.debug("AgentConfigScreen mounted")
        # Focus the agent selector for keyboard navigation
        try:
            self.query_one(AgentSelector).focus()
        except Exception as e:
            logger.warning(f"Failed to focus AgentSelector: {e}")

    async def on_agent_selector_agent_selected(self, message: AgentSelector.AgentSelected) -> None:
        """Handle agent selection - fetch detailed schemas."""
        self.selected_agent = message.agent
        assistant_id = message.assistant_id
        graph_id = message.agent.get("graph_id", "unknown")

        logger.info(f"Agent selected: {graph_id} ({assistant_id})")

        # Fetch detailed schemas for selected agent
        try:
            logger.debug(f"Fetching schemas for {assistant_id}")
            schemas = await self.langgraph_service.get_agent_schemas(assistant_id)
            self.schemas = schemas

            # Update schema viewer with detailed context_schema
            viewer = self.query_one(SchemaViewer)
            viewer.update_schemas(schemas)

            # Switch to schema tab to show the details
            tabbed_content = self.query_one(TabbedContent)
            tabbed_content.active = "tab-schema"

            logger.info(f"Loaded schemas for {graph_id}, switching to Schema Viewer")
        except Exception as e:
            logger.error(f"Failed to fetch schemas for {assistant_id}: {e}")
            # Update viewer to show error
            viewer = self.query_one(SchemaViewer)
            viewer.update_schemas(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-close":
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Handle escape key."""
        self.dismiss(None)
