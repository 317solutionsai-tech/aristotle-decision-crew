# Make the agents permanent and live in the app (CrewAI AMP + AWS)

This is a ONE-TIME setup. After it is done, the app calls your agents forever,
for anyone, with no terminal. You never repeat the local server step again.

The shape of it:

    The app  ->  an AWS Lambda URL (holds your secret token)  ->  your crew on CrewAI AMP  ->  back

Three accounts/things are involved:
  - CrewAI AMP  (app.crewai.com)  - hosts and runs the agents
  - AWS         (console.aws.amazon.com) - runs the tiny relay (Lambda)
  - your model key (OpenAI) - added once on CrewAI AMP, never in the browser

Rough cost: CrewAI AMP has a free trial then a paid tier; AWS Lambda is effectively
free at demo volume; you pay normal OpenAI usage (cents per run).

===============================================================================
PHASE 1 - Put your crew on CrewAI AMP
===============================================================================
1. Push the aristotle-decision-crew folder to a GitHub repo.
   (Easiest with no git: github.com > New repository > "uploading an existing file"
    > drag in the whole aristotle-decision-crew contents, including the src folder.)
2. Go to app.crewai.com and sign up / log in.
3. Click "Deploy" / "Create Crew" and connect your GitHub account.
4. Pick the aristotle-decision-crew repository. AMP detects the crew automatically.
5. In the deployment's Environment Variables, add your model key:
       OPENAI_API_KEY = sk-...          (and optional MODEL = gpt-4o-mini)
6. Click Deploy and wait for it to finish (a few minutes).

===============================================================================
PHASE 2 - Copy your endpoint, token, and input names
===============================================================================
On your crew's detail page:
7. STATUS tab: copy two things and keep them safe:
       - the API URL, like   https://your-crew-name.crewai.com
       - the Bearer Token
8. Confirm the inputs your crew expects. In a browser or Postman, the GET /inputs
   endpoint of your crew lists them. Our app sends these four:
       decision, options, factors, leading_option
   If AMP shows different names, tell me and I will match them in the relay.

===============================================================================
PHASE 3 - Create the AWS relay (Lambda)
===============================================================================
9.  Go to console.aws.amazon.com, sign up if needed, search "Lambda", open it.
10. Click "Create function" > Author from scratch.
        Name:    aristotle-relay
        Runtime: Python 3.12
    Click Create function.
11. In the Code tab, open lambda_function.py, delete everything, and paste the
    ENTIRE contents of lambda_proxy.py (in this folder). Then click "Deploy".
12. Rename the handler if needed: Code tab > Runtime settings > Edit > Handler =
        lambda_function.handler
13. Configuration tab > Environment variables > Edit > add two:
        CREW_URL   = https://your-crew-name.crewai.com     (no trailing slash)
        CREW_TOKEN = the Bearer Token from Phase 2
    Save.
14. Configuration tab > General configuration > Edit > Timeout = 2 min 0 sec. Save.
15. Configuration tab > Function URL > Create function URL:
        Auth type: NONE
        Configure CORS: tick it, Allow origin = *  , Allow headers = content-type ,
        Allow methods = POST and OPTIONS.
    Save. Copy the Function URL, like
        https://abcd1234.lambda-url.us-east-1.on.aws/

===============================================================================
PHASE 4 - Test the relay before touching the app
===============================================================================
16. Easiest test: paste your Function URL into the app's setting (Phase 5) and try
    the sample. Or use any REST tool to POST this body to the Function URL:
        {"decision":"Take the job or finish my masters?",
         "options":["Take the job","Finish the masters"],
         "factors":"Pay (5), Growth (4), Stress (3)",
         "leading_option":"Take the job"}
    A good response looks like:
        {"blind_spots":[...],"tradeoffs":{"gains":[...],"gives_up":[...]},"premortem":[...]}
    If you get the empty fallback, check the Lambda's CloudWatch logs and the
    CREW_URL / CREW_TOKEN values.

===============================================================================
PHASE 5 - Point the app at the relay (this makes it permanent)
===============================================================================
17. In Aristotle-Decision-Coach_CHALLENGE3.html find this line near the Step 4 code:
        const AGENTS_API="";
    Change it to your Function URL plus nothing else, e.g.:
        const AGENTS_API="https://abcd1234.lambda-url.us-east-1.on.aws/";
    (Send me the URL and I will edit and re-verify the file for you.)
18. Open the app, hard-refresh (Ctrl+F5), Try a sample decision > Step 4 >
    "AI second opinions". It now shows real CrewAI output every time, for anyone,
    with no terminal. If the relay is ever down, the app quietly falls back to the
    on-device version, so a demo never breaks.

===============================================================================
PHASE 6 - (Optional) host the app on a public link
===============================================================================
19. AWS S3 > create a bucket > enable static website hosting > upload the HTML.
20. Put CloudFront in front for HTTPS, or just share the S3 website URL for a demo.
    The app is a single file, so this is a drag-and-drop upload.

===============================================================================
NOTES
===============================================================================
- The deterministic engine still owns the score. The agents only add language and
  blind-spots. The human still makes the final call. Keep saying this to judges.
- The on-device agents stay as the built-in fallback, so the app works offline too.
- Keep your OPENAI_API_KEY and CREW_TOKEN private. They live on AMP and AWS, never
  in the HTML.
