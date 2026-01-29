"""A Class for creating a smiple smolagent multi-agent group.
create_agent_class returns a fully initialized class with two sub-agents and a manger agent.
"""

from typing import Dict, List, Any
from smolagents import (
    tool,
    RunResult,
    Tool,
    CodeAgent,
    InferenceClientModel,
    DuckDuckGoSearchTool,
    VisitWebpageTool,
    FinalAnswerTool,
    WikipediaSearchTool,
)

from Py_BackEnd.Agents.utils import document_request


class SmolAgentMulti:
    """
    SmolAgentMulti is a multi-agent orchestration class that manages a collection of sub-agents
    and a single manager agent.
    To use, initialize the class, and inject any functionality as tools.
    Could be expanded to be more generic, but this is just a template for how it would work.

    Attributes:
        sub_agents (Dict[str, CodeAgent]): Dictionary mapping agent names to CodeAgent instances.
        manager (CodeAgent): The manager agent that oversees and coordinates sub-agents.
    Methods:
        add_sub_agent(agent: CodeAgent) -> None:
            Registers a new sub-agent. The agent must have a name attribute.
        add_manager(agent: CodeAgent, managed_agents: List[str] = []) -> None:
            Registers a manager agent and optionally specifies which sub-agents it manages.
            If managed_agents is empty, the manager is assigned all sub-agents.
            The class assumes a single manager.
        inject_tool(agent_name: str, tool: Tool) -> None:
            Dynamically injects a tool into a specific agent (sub-agent or manager).
        agent_factory(tools: list[Tool], name: str, description: str, verbosity: int = 0,
                      max_steps: int = 2, **kwargs: Any) -> CodeAgent:
            Static factory method that creates and returns a new CodeAgent instance
            with the specified configuration and InferenceClientModel.
    """

    def __init__(self) -> None:
        self.sub_agents: Dict[str, CodeAgent] = {}
        self.manager: CodeAgent | None = None

    def add_sub_agent(self, agent: CodeAgent):
        assert agent.name, f"agent must have a name! \n{agent.__dict__}"
        self.sub_agents[agent.name] = agent

    def add_manager(self, agent: CodeAgent, managed_agents: List[str] = []):
        assert self.sub_agents != False, ValueError(
            "manager agent expects sub_agents, please add those first"
        )
        assert self.manager == None, ValueError(
            "manager already set"
        )  # we are assuming one manager for simplicity

        self.manager = agent
        if not managed_agents:
            self.manager.managed_agents = self.sub_agents
        else:
            for a in managed_agents:
                self.manager.managed_agents.append(self.sub_agents[a])

    def inject_tool(self, agent_name: str, tool: Tool):
        """
        We need this function to inject the db connection here to avoid cyclical dependencies. Or
        alternatively a method could just take a callable and add it to the web agent as a hardcoded implementation
        """
        if agent := self.sub_agents.get(agent_name, False):
            agent.tools.append(tool)
        elif agent_name == self.manager.name:
            self.manager.tools.append(tool)
        else:
            raise NameError("agent name not found")

    @staticmethod
    def agent_factory(
        tools: list[Tool],
        name: str,
        description: str,
        verbosity: int = 0,
        max_steps: int = 2,
        **kwargs: Any,
    ):
        return CodeAgent(
            model=InferenceClientModel(),
            tools=tools,
            name=name,
            description=description,
            verbosity_level=verbosity,
            max_steps=max_steps,
            **kwargs,
        )

    def run(self, query: str, return_full_result: bool = False) -> RunResult:
        assert self.manager, ValueError("manager not set")
        query_agent: str = f"""
            give the answer to the following query while including in your answer any error raised by other systems, agents or tools used.
            {query}
        """
        return self.manager.run(task=query_agent, return_full_result=return_full_result)


def create_agent_class():
    SmolAgents = SmolAgentMulti()

    SmolAgents.add_sub_agent(
        SmolAgents.agent_factory(
            [DuckDuckGoSearchTool(), VisitWebpageTool(), WikipediaSearchTool()],
            name="web_agent",
            description="An agent which searches the internet for information on a query",
            max_steps=4,
        )
    )

    SmolAgents.add_sub_agent(
        SmolAgents.agent_factory(
            tools=[tool(document_request)],
            name="rag_agent",
            description="An agent which queries a vector database for relevant information",
            max_steps=2,
        )
    )

    SmolAgents.add_manager(
        SmolAgents.agent_factory(
            name="manager",
            tools=[FinalAnswerTool()],
            description="managing agent",
            verbosity=2,
            max_steps=5,
            planning_interval=5,
            final_answer_checks=[],
        )
    )
    return SmolAgents
