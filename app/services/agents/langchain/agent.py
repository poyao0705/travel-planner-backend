from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_openrouter import ChatOpenRouter

model = ChatOpenRouter(model="anthropic/claude-sonnet-4.6",
    temperature=0,
    max_tokens=1024,)

def build_graph_config(thread_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": thread_id}}


def llm_node(state: MessagesState, config: RunnableConfig):
    response = model.invoke(state["messages"], config=config)
    return {"messages": [response]}

builder = StateGraph(MessagesState, )
builder.add_node("llm_node", llm_node)
builder.add_edge(START, "llm_node")
builder.add_edge("llm_node", END)

graph = builder.compile()