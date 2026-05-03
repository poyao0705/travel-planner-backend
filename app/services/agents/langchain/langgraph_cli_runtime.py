from app.services.agents.langchain.agent import build_graph
from app.services.agents.langchain.utils.tools import build_tools

graph = build_graph(build_tools())
