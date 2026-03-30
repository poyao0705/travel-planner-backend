from uuid import uuid4

from agno.run.workflow import WorkflowRunEvent

from app.services.agents.agno.steps import FOLLOW_UP_AGENT_NAME, PLANNING_STEP_NAME
from app.services.agents.stream import StreamEvent


VISIBLE_STEP_NAMES = frozenset({FOLLOW_UP_AGENT_NAME, PLANNING_STEP_NAME})



async def agno_events_to_internal(events, *, workflow, session_id: str):
    text_part_id = f"text_{uuid4().hex}"
    text_started = False

    async for event in events:
        if getattr(event, "event", "") != WorkflowRunEvent.step_completed.value:
            continue

        step_name = getattr(event, "step_name", None)
        content = getattr(event, "content", None)

        if step_name not in VISIBLE_STEP_NAMES:
            continue

        if not isinstance(content, str) or not content.strip():
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