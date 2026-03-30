# travel-planner-backend
An AI agent for travel planning

## Chat runtimes

The chat endpoint accepts an optional `runtime` field in the request body.

- `"langchain"` is the current default runtime for testing.
- `"agno"` is available as an explicit override.
- `"adk"` is accepted as a backward-compatible alias for `"agno"`.

The LangChain chat endpoint also supports an internal graph selector.

- Default graph: `stable`
- Supported graph variants: `stable`, `experimental`, `langgraph-v2`
- Selector inputs:
	- request header `x-internal-graph`
	- request body field `graph`
- Non-stable variants are only allowed when either:
	- the app is running in `APP_ENV=development` / `ENVIRONMENT=development` / `FASTAPI_ENV=development`
	- the request includes `x-internal-graph-secret` matching `INTERNAL_GRAPH_SECRET`

The LangChain runtime currently requires `OPENROUTER_API_KEY` because the coordinator and specialist models are created through `langchain-openrouter`.

Optional model overrides:

- `STREAM_LLM_MODEL` controls the user-facing streaming model. Default: `anthropic/claude-sonnet-4.5`
- `EXTRACTOR_LLM_MODEL` controls the lightweight structured extractor model. Default: `anthropic/claude-3.5-haiku`
- `MAP_AGENT_LLM_MODEL` controls the map agent model. Default: `anthropic/claude-sonnet-4.5`
