# travel-planner-backend
An AI agent for travel planning

## Chat runtimes

The chat endpoint accepts an optional `runtime` field in the request body.

- `"langchain"` is the current default runtime for testing.
- `"adk"` remains available as an explicit override.

The LangChain runtime currently requires `OPENROUTER_API_KEY` because the coordinator and specialist models are created through `langchain-openrouter`.

Optional model overrides:

- `STREAM_LLM_MODEL` controls the user-facing streaming model. Default: `anthropic/claude-sonnet-4.5`
- `EXTRACTOR_LLM_MODEL` controls the lightweight structured extractor model. Default: `anthropic/claude-3.5-haiku`
- `MAP_AGENT_LLM_MODEL` controls the map agent model. Default: `anthropic/claude-sonnet-4.5`
