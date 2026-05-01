from langchain_tavily import TavilySearch


def build_tools():
    web_search_tool = TavilySearch(
        max_results=5,
        topic="general",
    )
    return [web_search_tool]
