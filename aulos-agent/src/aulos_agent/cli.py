"""Operator CLI for the aulos agent."""

from __future__ import annotations

import argparse
import uuid

from langchain_core.messages import HumanMessage

from aulos_agent.config.settings import get_settings
from aulos_agent.graph.builder import build_graph


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Aulos LangGraph agent")
    parser.add_argument("prompt", nargs="?", help="User prompt to send to the agent")
    parser.add_argument(
        "--thread-id",
        default=None,
        help="Conversation thread id (default: random UUID)",
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Print effective provider/model settings and exit",
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    if args.show_config:
        print(
            f"provider={settings.llm_provider} model={settings.llm_model} "
            f"tracing={settings.langchain_tracing_v2}"
        )
        return 0

    if not args.prompt:
        parser.error("prompt is required unless --show-config is set")

    if settings.llm_provider != "fake":
        settings.require_live_credentials()

    graph = build_graph(settings=settings)
    thread_id = args.thread_id or str(uuid.uuid4())
    result = graph.invoke(
        {"messages": [HumanMessage(content=args.prompt)]},
        config={
            "configurable": {"thread_id": thread_id},
            "recursion_limit": settings.recursion_limit,
        },
    )
    last = result["messages"][-1]
    content = getattr(last, "content", str(last))
    print(content)
    print(f"\n[thread_id={thread_id}]", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
