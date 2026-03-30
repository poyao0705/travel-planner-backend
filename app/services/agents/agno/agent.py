from agno.os import AgentOS
from app.services.agents.agno.workflow import travel_planner_workflow


workflow = travel_planner_workflow


agent_os = AgentOS(workflows=[workflow])
app = agent_os.get_app()