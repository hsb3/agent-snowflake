"""Stream processing subgraphs.

This package contains fine-grained subgraphs for stream processing.
Each subgraph breaks down complex operations into small, focused nodes.
"""

from .stream_processor import build_stream_processor_subgraph

__all__ = ["build_stream_processor_subgraph"]
