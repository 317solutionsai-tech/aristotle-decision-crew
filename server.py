# Web API around the decision crew. The app calls POST /review and gets JSON back.
# Local test:   pip install "crewai[tools]" fastapi uvicorn
#               set your key, then:  python -m uvicorn server:app --port 8000
# Then in the app set AGENTS_API = "http://localhost:8000/review"
import os, json, re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from crewai import Agent, Task, Crew, Process, LLM

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def run_crew(d):
    llm = LLM(model=os.getenv("MODEL", "gpt-4o-mini"))
    decision = d.get("decision",""); options = d.get("options",[]); 
    factors = d.get("factors",""); lead = d.get("leading_option","")
    opts = ", ".join(options) if isinstance(options, list) else str(options)
    blindspot = Agent(role="Blind-spot finder", goal="Surface considerations the user did not list. Never pick a winner.",
        backstory="The engine already ranked the options; that is fixed. You only name what is missing.", llm=llm, verbose=False)
    explainer = Agent(role="Tradeoff explainer", goal="Explain the leading option's gains and gives-up in plain words, using only the user's factors.",
        backstory="You invent no new facts and no new winner.", llm=llm, verbose=False)
    premortem = Agent(role="Premortem analyst", goal="List realistic ways the leading option could fail within a year.",
        backstory="You help the human see risks; you do not change the decision.", llm=llm, verbose=False)
    assembler = Agent(role="Output assembler", goal="Return strict JSON only, with no winner.",
        backstory="You output only valid JSON.", llm=llm, verbose=False)
    t1 = Task(description=f"Decision: {decision}\nOptions: {opts}\nFactors (0-5): {factors}\nLeading option (fixed): {lead}\nList 3-5 considerations the user did NOT include. Do not pick a winner.",
              expected_output="3-5 short bullets.", agent=blindspot)
    t2 = Task(description=f"For {lead}, explain gains and gives-up using only these factors: {factors}.",
              expected_output="Gains (2-3) and Gives up (2-3).", agent=explainer)
    t3 = Task(description=f"Imagine {lead} failed a year later. List 3 likely reasons, specific to: {decision}.",
              expected_output="3 failure modes.", agent=premortem)
    t5 = Task(description="Combine into one JSON object. No winner.",
              expected_output='{"blind_spots":["..."],"tradeoffs":{"gains":["..."],"gives_up":["..."]},"premortem":["..."]}',
              agent=assembler, context=[t1,t2,t3])
    crew = Crew(agents=[blindspot,explainer,premortem,assembler], tasks=[t1,t2,t3,t5], process=Process.sequential, verbose=False)
    res = str(crew.kickoff())
    try:
        return json.loads(res)
    except Exception:
        m = re.search(r"\{.*\}", res, re.S)
        return json.loads(m.group(0)) if m else {"blind_spots":[],"tradeoffs":{"gains":[],"gives_up":[]},"premortem":[]}

@app.get("/")
def health(): return {"ok": True, "service": "aristotle decision crew"}

@app.post("/review")
async def review(req: Request):
    return run_crew(await req.json())
