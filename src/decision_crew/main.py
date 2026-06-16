#!/usr/bin/env python
try:
    from dotenv import load_dotenv; load_dotenv()
except Exception:
    pass
from decision_crew.crew import DecisionCrew

# This is what the app would pass in. The engine already scored it; the leading option is a FACT.
DECISION = {
    "decision": "Take the Austin job now, or finish my one-year master's?",
    "options": "Take the job; Finish the master's; Defer and do both later",
    "factors": "Long-term earning (4), Learning and growth (4), Financial risk now (3), Freedom (3), Stress and wellbeing (3), Meaning (3)",
    "leading_option": "Take the job",
}

def run():
    DecisionCrew().crew().kickoff(inputs=DECISION)

if __name__ == "__main__":
    run()
