"""Memory / checkpointer helpers."""

from langgraph.checkpoint.memory import MemorySaver


def create_checkpointer() -> MemorySaver:
    """Sprint-0: in-process thread memory. Swap for durable saver later."""
    return MemorySaver()
