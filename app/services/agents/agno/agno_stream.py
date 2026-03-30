from uuid import uuid4

from agno.run.agent import RunEvent
from agno.run.workflow import WorkflowRunEvent

from app.services.agents.agno.steps import FOLLOW_UP_AGENT_NAME, PLANNING_STEP_NAME
from app.services.agents.stream import StreamEvent


VISIBLE_STEP_NAMES = frozenset({FOLLOW_UP_AGENT_NAME, PLANNING_STEP_NAME})


async def agno_events_to_internal(events, *, workflow, session_id: str):
    text_part_id = f"text_{uuid4().hex}"
    text_started = False
    current_step_name = None

    async for event in events:
        event_type = getattr(event, "event", "")

        if event_type == WorkflowRunEvent.step_started.value:
            current_step_name = getattr(event, "step_name", None)
            continue

        if event_type == WorkflowRunEvent.step_completed.value:
            current_step_name = None
            continue

        # Only yield RunContentEvent — these are the token deltas.
        # RunCompletedEvent also has `content` but carries the full accumulated
        # response, which would duplicate everything already streamed.
        if event_type != RunEvent.run_content.value:
            continue

        if current_step_name not in VISIBLE_STEP_NAMES:
            continue

        content = getattr(event, "content", None)
        if not isinstance(content, str) or not content:
            continue

        if not text_started:
            yield StreamEvent.text_start(text_part_id)
            text_started = True

        yield StreamEvent.text_delta(text_part_id, content)

    if text_started:
        yield StreamEvent.text_end(text_part_id)

    yield StreamEvent.ui(
        {"session_state": workflow.get_session_state(session_id=session_id) or {}}
    )