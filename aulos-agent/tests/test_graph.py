"""Graph compile and invoke tests (offline)."""

from langchain_core.messages import AIMessage, HumanMessage

from aulos_agent.config.settings import Settings
from aulos_agent.graph.builder import build_graph
from aulos_agent.llm.factory import DeterministicFakeChatModel


def test_graph_compiles_and_invokes_offline():
    settings = Settings(AULOS_LLM_PROVIDER="fake")
    model = DeterministicFakeChatModel(responses=["offline-ok"])
    graph = build_graph(settings=settings, model=model, tools=[])

    result = graph.invoke(
        {"messages": [HumanMessage(content="hello")]},
        config={"configurable": {"thread_id": "test-thread-1"}},
    )

    last = result["messages"][-1]
    assert isinstance(last, AIMessage)
    assert last.content == "offline-ok"


def test_thread_continuity_with_checkpointer():
    settings = Settings(AULOS_LLM_PROVIDER="fake")
    model = DeterministicFakeChatModel(responses=["first", "second"])
    graph = build_graph(settings=settings, model=model, tools=[])
    config = {"configurable": {"thread_id": "test-thread-2"}}

    graph.invoke({"messages": [HumanMessage(content="hi")]}, config=config)
    result = graph.invoke({"messages": [HumanMessage(content="again")]}, config=config)

    human_count = sum(1 for m in result["messages"] if isinstance(m, HumanMessage))
    assert human_count >= 2
