from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig

# from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition


# TODO: add this back in production
# checkpointer = InMemorySaver()
def build_graph_config(thread_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": thread_id}}


def build_graph(tools):
    model = init_chat_model(
        model_provider="openrouter",
        model="openai/gpt-5.4",
        temperature=0,
        max_tokens=1024,
    ).bind_tools(tools)

    def llm_node(state: MessagesState, config: RunnableConfig):
        response = model.invoke(state["messages"], config=config)
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("llm_node", llm_node)
    builder.add_node("tools", ToolNode(tools=tools))
    builder.add_edge(START, "llm_node")
    builder.add_conditional_edges(
        "llm_node",
        tools_condition,
        {
            "tools": "tools",
            END: END,
        },
    )
    builder.add_edge("tools", "llm_node")
    builder.add_edge("llm_node", END)

    return builder.compile()
