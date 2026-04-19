from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_openrouter import ChatOpenRouter

model = ChatOpenRouter(model="anthropic/claude-sonnet-4.6",
    temperature=0,
    max_tokens=1024,)

def llm_node(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": [response]}

builder = StateGraph(MessagesState, )
builder.add_node("llm_node", llm_node)
builder.add_edge(START, "llm_node")
builder.add_edge("llm_node", END)

graph = builder.compile()