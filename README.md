# travel-planner-backend
An AI agent for travel planning

## Chat runtimes

The chat endpoint accepts an optional `runtime` field in the request body.

- `"langchain"` is the current default runtime for testing.
- `"adk"` remains available as an explicit override.

The LangChain runtime currently requires `OPENROUTER_API_KEY` because the coordinator and specialist models are created through `langchain-openrouter`.
