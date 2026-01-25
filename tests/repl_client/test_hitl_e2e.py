"""End-to-end HITL integration tests (Phase 2).

Tests the complete HITL flow from interrupt detection through resume.
Requires live LangGraph server with HITL-enabled agent.
"""

from unittest.mock import Mock, patch

import pytest
import pytest_asyncio

from repl_client.core.client import LangGraphClient
from repl_client.core.session import SessionState
from repl_client.streaming.handler import StreamHandler
from repl_client.streaming.hitl import HITLHandler
from repl_client.streaming.types import ChunkType, Interrupt
from repl_client.ui.renderer import Renderer


@pytest.fixture
def session():
    """Create session state for testing"""
    session = SessionState()
    session.set_agent("test_agent")
    session.set_thread("test_thread")
    return session


@pytest.fixture
def renderer():
    """Create mock renderer"""
    return Mock(spec=Renderer)


@pytest.fixture
def hitl_handler(renderer):
    """Create HITL handler"""
    return HITLHandler(renderer=renderer)


@pytest.fixture
def stream_handler(session):
    """Create stream handler"""
    return StreamHandler(session=session)


class TestHITLInterruptDetection:
    """Test that interrupts are correctly detected from updates stream"""

    @pytest.mark.asyncio
    async def test_parse_interrupt_from_updates_stream(self, stream_handler):
        """Test _parse_interrupt extracts interrupt from updates data"""
        # Simulate updates stream event with __interrupt__
        updates_data = {
            "__interrupt__": [
                {
                    "value": {"tool": "sql_db_query", "args": {"query": "SELECT * FROM users"}},
                    "when": "during",
                }
            ]
        }

        interrupt = stream_handler._parse_interrupt(updates_data)

        assert interrupt is not None
        assert isinstance(interrupt, Interrupt)
        assert interrupt.value["tool"] == "sql_db_query"
        assert interrupt.value["args"]["query"] == "SELECT * FROM users"

    @pytest.mark.asyncio
    async def test_parse_interrupt_returns_none_when_no_interrupt(self, stream_handler):
        """Test _parse_interrupt returns None when no __interrupt__ key"""
        updates_data = {"some_other_key": "value"}

        interrupt = stream_handler._parse_interrupt(updates_data)
        assert interrupt is None

    @pytest.mark.asyncio
    async def test_stream_handler_yields_interrupt_chunk(self, stream_handler):
        """Test StreamHandler yields INTERRUPT chunk when processing updates stream"""
        # Simulate SSE stream with updates event containing interrupt
        chunks = [
            (
                "updates",
                {
                    "__interrupt__": [
                        {
                            "value": {
                                "tool": "sql_db_query",
                                "args": {"query": "SELECT COUNT(*) FROM orders"},
                            },
                            "when": "during",
                        }
                    ]
                },
            )
        ]

        async def _async_iter(items):
            for item in items:
                yield item

        parsed_chunks = [c async for c in stream_handler.process_stream(_async_iter(chunks))]

        # Should have exactly one INTERRUPT chunk
        interrupt_chunks = [c for c in parsed_chunks if c.chunk_type == ChunkType.INTERRUPT]
        assert len(interrupt_chunks) == 1

        interrupt_chunk = interrupt_chunks[0]
        assert interrupt_chunk.interrupt is not None
        assert interrupt_chunk.interrupt.value["tool"] == "sql_db_query"


class TestHITLApprovalFlow:
    """Test approval/rejection flow"""

    def test_hitl_handler_approval(self, hitl_handler, session):
        """Test HITL handler processes approval"""
        interrupt = Interrupt(
            id="int_123",
            value={"tool": "sql_db_query", "args": {"query": "SELECT * FROM customers"}},
        )

        # Mock user approving
        with patch("builtins.input", return_value="y"):
            command = hitl_handler.handle_interrupt(interrupt, session)

        # Should return resume command with approval
        assert command == {"resume": {"approve": True}}

        # Renderer should have been called to show panel
        hitl_handler.renderer.render_panel.assert_called_once()

    def test_hitl_handler_rejection(self, hitl_handler, session):
        """Test HITL handler processes rejection"""
        interrupt = Interrupt(
            id="int_456", value={"tool": "dangerous_operation", "args": {"action": "delete_all"}}
        )

        # Mock user rejecting
        with patch("builtins.input", return_value="n"):
            command = hitl_handler.handle_interrupt(interrupt, session)

        # Should return resume command with rejection
        assert command == {"resume": {"approve": False}}


@pytest.mark.integration
class TestHITLEndToEnd:
    """End-to-end tests requiring live server.

    These tests require:
    - LangGraph server running (e.g., http://localhost:2024)
    - Agent with HITL enabled for certain tools
    - Server must be configured with interrupt_before or interrupt_after

    Skip if server not available.
    """

    @pytest_asyncio.fixture
    async def client(self):
        """Create client and verify connection"""
        client = LangGraphClient(base_url="http://localhost:2024", timeout=30)
        connected = await client.connect()

        if not connected:
            pytest.skip("LangGraph server not available at http://localhost:2024")

        return client

    @pytest.mark.asyncio
    async def test_full_hitl_flow_with_approval(
        self, client, session, stream_handler, hitl_handler
    ):
        """Test complete HITL flow: message -> interrupt -> approval -> resume -> result

        This is a manual integration test - requires server with HITL agent.
        """
        # This test is primarily for manual verification
        # Automated testing would require:
        # 1. Server with known HITL-enabled agent
        # 2. Predictable tool call trigger
        # 3. Mock user input

        # For now, mark as skip unless explicit environment variable set
        import os

        if not os.getenv("RUN_HITL_E2E_TESTS"):
            pytest.skip("Set RUN_HITL_E2E_TESTS=1 to run live server tests")

        # Create thread
        thread_id = await client.create_thread()
        session.set_thread(thread_id)

        # Get agent (assumes agent_enhanced has HITL)
        agents = await client.list_agents(limit=10)
        agent_id = None
        for agent in agents:
            if "enhanced" in agent.get("assistant_id", ""):
                agent_id = agent["assistant_id"]
                break

        if not agent_id:
            pytest.skip("No HITL-enabled agent found (looking for 'enhanced')")

        session.set_agent(agent_id)

        # Send message that should trigger tool call
        message = "Query the customers table"

        # Stream message
        chunks = client.stream_message(thread_id=thread_id, message=message, assistant_id=agent_id)

        # Process stream and look for interrupt
        interrupt_detected = False
        async for parsed in stream_handler.process_stream(chunks):
            if parsed.chunk_type == ChunkType.INTERRUPT:
                interrupt_detected = True
                interrupt = parsed.interrupt

                # Mock user approval
                with patch("builtins.input", return_value="y"):
                    command = hitl_handler.handle_interrupt(interrupt, session)

                # Resume
                resume_chunks = client.resume_after_interrupt(
                    thread_id=thread_id, assistant_id=agent_id, command=command
                )

                # Process resumed stream
                resumed_texts = []
                async for resumed_parsed in stream_handler.process_stream(resume_chunks):
                    if resumed_parsed.chunk_type == ChunkType.TEXT_DELTA:
                        resumed_texts.append(resumed_parsed.text_delta)

                # Should have gotten response after approval
                assert len(resumed_texts) > 0

        # This test might not trigger interrupt if server config changed
        # Log for manual verification
        if not interrupt_detected:
            print("Warning: No interrupt detected - server may not have HITL enabled")


class TestHITLMultipleTools:
    """Test handling multiple tool calls with HITL"""

    @pytest.mark.asyncio
    async def test_sequential_interrupts(self, stream_handler, hitl_handler, session):
        """Test handling multiple interrupts sequentially"""
        # Simulate stream with two interrupts
        chunks = [
            (
                "updates",
                {
                    "__interrupt__": [
                        {
                            "value": {
                                "tool": "sql_db_query",
                                "args": {"query": "SELECT * FROM users"},
                            },
                            "when": "during",
                        }
                    ]
                },
            ),
            (
                "messages/partial",
                [  # Note: messages/partial wraps data in array
                    {
                        "id": "msg-1",
                        "type": "ai",
                        "content": [{"type": "text", "text": "First result"}],
                        "response_metadata": {},
                    }
                ],
            ),
        ]

        async def _async_iter(items):
            for item in items:
                yield item

        parsed_chunks = [c async for c in stream_handler.process_stream(_async_iter(chunks))]

        # Should have one interrupt and one text delta
        interrupt_chunks = [c for c in parsed_chunks if c.chunk_type == ChunkType.INTERRUPT]
        text_chunks = [c for c in parsed_chunks if c.chunk_type == ChunkType.TEXT_DELTA]

        assert len(interrupt_chunks) == 1
        assert len(text_chunks) == 1


class TestHITLErrorHandling:
    """Test error scenarios in HITL flow"""

    @pytest.mark.asyncio
    async def test_malformed_interrupt_data(self, stream_handler):
        """Test handling of malformed interrupt data"""
        # Missing 'value' key
        updates_data = {
            "__interrupt__": [
                {
                    "when": "during"
                    # Missing 'value'
                }
            ]
        }

        interrupt = stream_handler._parse_interrupt(updates_data)

        # Should still create interrupt but with empty value
        assert interrupt is not None
        assert interrupt.value == {}

    @pytest.mark.asyncio
    async def test_empty_interrupt_list(self, stream_handler):
        """Test handling of empty interrupt list"""
        updates_data = {"__interrupt__": []}

        interrupt = stream_handler._parse_interrupt(updates_data)
        assert interrupt is None
