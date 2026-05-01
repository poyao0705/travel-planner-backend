from langchain_core.runnables import RunnableConfig
from langchain_openrouter import ChatOpenRouter

# from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.services.agents.langchain.utils.tools import TOOLS


# TODO: add this back in production
# checkpointer = InMemorySaver()
def build_graph_config(thread_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": thread_id}}


model = ChatOpenRouter(
    model="anthropic/claude-sonnet-4.6",
    temperature=0,
    max_tokens=1024,
).bind_tools(TOOLS)


def llm_node(state: MessagesState, config: RunnableConfig):
    response = model.invoke(state["messages"], config=config)
    return {"messages": [response]}


builder = StateGraph(MessagesState)
builder.add_node("llm_node", llm_node)
builder.add_node("tools", ToolNode(tools=TOOLS))
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

graph = builder.compile()
