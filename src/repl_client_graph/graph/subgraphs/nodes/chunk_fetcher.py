"""Chunk fetcher node - fetch next chunk from stream."""


def fetch_next_chunk_node(state: dict) -> dict:
    """Fetch next chunk from stream_chunks list.

    Retrieves the chunk at current chunk_index and increments the index.
    If no chunks remain, sets current_chunk to None.

    Args:
        state: Subgraph state with stream_chunks and chunk_index

    Returns:
        Updated state with current_chunk and incremented chunk_index
    """
    chunks = state.get("stream_chunks", [])
    index = state.get("chunk_index", 0)

    # DEBUG
    import sys

    print(f"[FETCH] Index={index}, Total={len(chunks)}", file=sys.stderr, flush=True)

    # Get chunk at current index
    current_chunk = None
    if index < len(chunks):
        current_chunk = chunks[index]
        print(
            f"[FETCH] Got chunk: {current_chunk[0] if current_chunk else None}",
            file=sys.stderr,
            flush=True,
        )

    return {
        **state,
        "current_chunk": current_chunk,
        "chunk_index": index + 1,
    }


def check_has_more_chunks(state: dict) -> str:
    """Conditional edge: check if more chunks remain.

    This edge is used after processing a chunk to decide whether to
    fetch the next chunk or exit the subgraph.

    Args:
        state: Subgraph state with chunk_index and stream_chunks

    Returns:
        "more" if chunks remain, "done" otherwise
    """
    chunks = state.get("stream_chunks", [])
    index = state.get("chunk_index", 0)

    # Check if there are more chunks to process
    if index < len(chunks):
        return "more"
    else:
        return "done"
