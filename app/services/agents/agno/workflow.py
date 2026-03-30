from agno.db.in_memory import InMemoryDb
from agno.workflow import Workflow

from app.services.agents.agno.router import planner_route
from app.services.agents.agno.steps import extraction_agent


travel_planner_workflow = Workflow(
    name="Travel Planning Workflow",
    steps=[extraction_agent, planner_route],
    db=InMemoryDb(),
)