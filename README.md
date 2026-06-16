# Aristotle decision crew (the generative layer)

The real CrewAI crew behind the app's AI second opinions. It takes a decision the
engine has ALREADY scored and only adds language. It never picks a winner.

Agents:
- blindspot_agent     surfaces considerations the user did not list
- explainer_agent     explains the leading option's gains and gives-up in plain words
- premortem_agent     lists realistic failure modes
- judge_agent         (pitch prep) asks tough judge questions
- assembler_agent     returns clean JSON the app can read (decision_review.json)

Human-in-the-loop: the engine owns the score, the human commits. The agents are advisory.

## Run it (easy, single file)
From the project folder:
    python run_decision_crew.py
It will ask for your API key, run the crew, print the output, and save decision_review.json.

## Run it (full CrewAI project)
    pip install "crewai[tools]"
    copy .env.example to .env and add your key
    crewai run     (or)   python -m decision_crew.main

## Where it runs in production
Behind an AWS Lambda calling Amazon Bedrock, or deployed to CrewAI AMP, so no API key
sits in the browser. The single HTML app keeps curated fallback text so the demo works offline.

---

## Making the agents LIVE inside the app (no terminal at demo time)

The app file has one setting near the Step 4 code:
    const AGENTS_API = "";
Leave it empty and the app uses the on-device (rule-based) agents. Paste a URL and the app calls the real CrewAI agents, with automatic fallback to the on-device version if the call fails.

### A. Prove it live on your machine first (5 min, free)
1. pip install "crewai[tools]" fastapi "uvicorn[standard]"
2. Set your model key:  (mac/linux) export OPENAI_API_KEY=sk-...   (windows) setx OPENAI_API_KEY "sk-..."
3. python -m uvicorn server:app --port 8000
4. In the app set AGENTS_API = "http://localhost:8000/review", hard-refresh, open Step 4. The "AI second opinions" panel now shows real agent output.

### B. Host it so it works for anyone (no terminal)
Easiest AWS path is App Runner (it builds the included Dockerfile and gives you an HTTPS URL):
1. Push aristotle-decision-crew/ to GitHub.
2. AWS Console > App Runner > Create service > Source: your repo (or Container).
3. Add your model key as an environment variable / secret (OPENAI_API_KEY, or Bedrock settings).
4. Deploy. Copy the service URL, e.g. https://xxxx.awsapprunner.com
5. In the app set AGENTS_API = "https://xxxx.awsapprunner.com/review".
6. Host the app HTML on S3 + CloudFront. Done: live agents, no terminal.

(CrewAI AMP alternative: deploy the crew on app.crewai.com for a hosted endpoint, then point a tiny Lambda proxy at it so the AMP token stays server-side, and set AGENTS_API to the Lambda URL.)

The deterministic engine still owns the score; the agents only add language and blind-spots; the human still makes the final call.
