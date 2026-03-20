from google.adk.agents import LlmAgent
from ddgs import DDGS


# 1. Define your Search Tool
def web_search(query: str) -> str:
    """Searches the web for up-to-date information to answer user questions."""
    # We fetch the top 3 results for speed and context
    results = DDGS().text(query, max_results=3)
    return str(list(results)) if results else "No results found."


# 2. Build the Agent
root_agent = LlmAgent(
    name="search_bot",
    model="gemini-2.5-flash",
    description="A helpful assistant with live web search capabilities.",
    instruction="""You are a friendly, concise assistant. 
    If a user asks about current events, facts, or anything you aren't 100% sure about, 
    ALWAYS use the `web_search` tool to find the answer before responding.""",
    tools=[web_search],
)
