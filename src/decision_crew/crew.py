import os
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

LLM_MODEL = os.getenv("MODEL", "gpt-4o-mini")


@CrewBase
class DecisionCrew:
    """Aristotle generative layer. Agents add language and surface blind spots.
    They never decide the ranking; the deterministic engine owns the score.

    Runtime crew = blindspot + explainer + premortem (run in parallel) -> assembler.
    The three analysis agents run concurrently to keep the response fast. The Judge
    agent is intentionally NOT in the runtime crew: its output is for pitch prep only
    and is never shown to the user, so running it would only add latency. Its config
    stays in agents.yaml / tasks.yaml for documentation and optional manual runs.
    """
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def _llm(self):
        return LLM(model=LLM_MODEL)

    @agent
    def blindspot_agent(self):
        return Agent(config=self.agents_config["blindspot_agent"], llm=self._llm(), verbose=False)

    @agent
    def explainer_agent(self):
        return Agent(config=self.agents_config["explainer_agent"], llm=self._llm(), verbose=False)

    @agent
    def premortem_agent(self):
        return Agent(config=self.agents_config["premortem_agent"], llm=self._llm(), verbose=False)

    @agent
    def assembler_agent(self):
        return Agent(config=self.agents_config["assembler_agent"], llm=self._llm(), verbose=False)

    # The three analysis tasks run in parallel (async_execution is set in tasks.yaml).
    @task
    def blindspot_task(self):
        return Task(config=self.tasks_config["blindspot_task"])

    @task
    def explainer_task(self):
        return Task(config=self.tasks_config["explainer_task"])

    @task
    def premortem_task(self):
        return Task(config=self.tasks_config["premortem_task"])

    # The assembler waits for all three (they are its context) and returns the JSON.
    @task
    def assemble_task(self):
        return Task(config=self.tasks_config["assemble_task"])

    @crew
    def crew(self):
        return Crew(
            agents=[self.blindspot_agent(), self.explainer_agent(), self.premortem_agent(), self.assembler_agent()],
            tasks=[self.blindspot_task(), self.explainer_task(), self.premortem_task(), self.assemble_task()],
            process=Process.sequential,
            verbose=False,
        )
