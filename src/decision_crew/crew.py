import os
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

LLM_MODEL = os.getenv("MODEL", "gpt-4o-mini")

@CrewBase
class DecisionCrew:
    """Aristotle generative layer. Agents add language; they never decide the score."""
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def _llm(self):
        return LLM(model=LLM_MODEL)

    @agent
    def blindspot_agent(self): return Agent(config=self.agents_config["blindspot_agent"], llm=self._llm(), verbose=True)
    @agent
    def explainer_agent(self): return Agent(config=self.agents_config["explainer_agent"], llm=self._llm(), verbose=True)
    @agent
    def premortem_agent(self): return Agent(config=self.agents_config["premortem_agent"], llm=self._llm(), verbose=True)
    @agent
    def judge_agent(self): return Agent(config=self.agents_config["judge_agent"], llm=self._llm(), verbose=True)
    @agent
    def assembler_agent(self): return Agent(config=self.agents_config["assembler_agent"], llm=self._llm(), verbose=True)

    @task
    def blindspot_task(self): return Task(config=self.tasks_config["blindspot_task"])
    @task
    def explainer_task(self): return Task(config=self.tasks_config["explainer_task"])
    @task
    def premortem_task(self): return Task(config=self.tasks_config["premortem_task"])
    @task
    def judge_task(self): return Task(config=self.tasks_config["judge_task"])
    @task
    def assemble_task(self): return Task(config=self.tasks_config["assemble_task"])

    @crew
    def crew(self):
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential, verbose=True)
