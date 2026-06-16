# Aristotle decision crew - single-file runner. No venv juggling.
# Run:  python run_decision_crew.py   (it asks for your API key)
import os, json

def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("\nPaste your OpenAI API key (starts with sk-), then press Enter:")
        os.environ["OPENAI_API_KEY"] = input("API key: ").strip()
    os.environ.setdefault("MODEL", "gpt-4o-mini")
    from crewai import Agent, Task, Crew, Process, LLM
    llm = LLM(model=os.environ["MODEL"])

    # The app passes this in. The engine ALREADY scored it; the leader is a fact the agents must not change.
    D = {
      "decision": "Take the Austin job now, or finish my one-year master's?",
      "options": "Take the job; Finish the master's; Defer and do both later",
      "factors": "Long-term earning (4), Learning and growth (4), Financial risk now (3), Freedom (3), Stress and wellbeing (3), Meaning (3)",
      "leading_option": "Take the job",
    }

    blindspot = Agent(role="Blind-spot finder",
        goal="Surface considerations the user did not list. Never re-rank or pick a winner.",
        backstory="A sharp decision coach. The engine already decided the ranking; that is fixed. You only point out what is missing.", llm=llm, verbose=True)
    explainer = Agent(role="Plain-language tradeoff explainer",
        goal="Explain what the leading option gains and gives up, using only the user's factors.",
        backstory="You translate the result into simple words. You invent no new facts and no new winner.", llm=llm, verbose=True)
    premortem = Agent(role="Premortem analyst",
        goal="List realistic ways the leading option could fail within a year.",
        backstory="You run a premortem (Klein, HBR 2007). You help the human see risks; you do not change the decision.", llm=llm, verbose=True)
    judge = Agent(role="Tough hackathon judge (pitch prep)",
        goal="Ask the hardest questions a judge would ask about this project.",
        backstory="Unsentimental AI-hackathon judge. This is for pitch prep, not the end user.", llm=llm, verbose=True)
    assembler = Agent(role="Output assembler",
        goal="Combine everything into strict JSON the app can read, with no winner.",
        backstory="You output only valid JSON, no extra text.", llm=llm, verbose=True)

    t1 = Task(description=f"Decision: {D['decision']}\nOptions: {D['options']}\nFactors (importance 0-5): {D['factors']}\nThe engine's leading option is {D['leading_option']} (fixed). List 3-5 important considerations the user did NOT include. Do not re-rank or pick a winner.",
              expected_output="3-5 missing considerations, each one sentence.", agent=blindspot)
    t2 = Task(description=f"For the leading option {D['leading_option']}, explain in plain language what the user gains and gives up, using ONLY these factors: {D['factors']}.",
              expected_output="Two short lists: Gains (2-3) and Gives up (2-3).", agent=explainer)
    t3 = Task(description=f"Imagine it is a year later and choosing {D['leading_option']} went badly. List the 3 most likely reasons, specific to: {D['decision']}.",
              expected_output="3 realistic failure modes, each one sentence.", agent=premortem)
    t4 = Task(description="Act as a tough hackathon judge. Ask the 4 hardest questions about this decision-coach project, focused on why it needs AI and its weakest claims.",
              expected_output="4 tough questions, numbered.", agent=judge, output_file="judge_questions.md")
    t5 = Task(description="Combine the blind spots, the gains/gives-up, and the premortem into one JSON object. Do NOT include a winner.",
              expected_output='Strict JSON: {"blind_spots":["..."],"tradeoffs":{"gains":["..."],"gives_up":["..."]},"premortem":["..."]}',
              agent=assembler, context=[t1,t2,t3], output_file="decision_review.json")

    crew = Crew(agents=[blindspot,explainer,premortem,judge,assembler], tasks=[t1,t2,t3,t4,t5], process=Process.sequential, verbose=True)
    result = crew.kickoff()
    print("\n\n===========  STRUCTURED OUTPUT (decision_review.json)  ===========\n")
    print(result)
    print("\n(Saved: decision_review.json for the app, judge_questions.md for pitch prep.)")

if __name__ == "__main__":
    main()
