"""
AWS Lambda relay between the app and your CrewAI AMP crew.

Why this exists: the browser must never hold your crew's secret token. This Lambda
holds it, calls the crew on AMP, waits for the result, and returns clean JSON to the app.

It uses only the Python standard library, so there is nothing to install or containerize.

Set two environment variables on the Lambda (Configuration > Environment variables):
    CREW_URL    = https://your-crew-name.crewai.com      (no trailing slash)
    CREW_TOKEN  = the Bearer token from your crew's Status tab

Turn on a Function URL (Configuration > Function URL) with Auth type NONE and CORS
allow-origins "*". Set the Lambda timeout to 2 minutes (Configuration > General).

The app sends: {"decision","options":[...],"factors","leading_option"}
This returns:  {"blind_spots":[...],"tradeoffs":{"gains":[...],"gives_up":[...]},"premortem":[...]}
"""
import os, json, time, re, urllib.request, urllib.error

CREW_URL = os.environ.get("CREW_URL", "").rstrip("/")
CREW_TOKEN = os.environ.get("CREW_TOKEN", "")
CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
    "Content-Type": "application/json",
}
FALLBACK = {"blind_spots": [], "tradeoffs": {"gains": [], "gives_up": []}, "premortem": []}


def _http(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + CREW_TOKEN)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def _extract_json(text):
    """Pull the {blind_spots, tradeoffs, premortem} object out of the crew's final text."""
    if isinstance(text, dict):
        obj = text
    else:
        try:
            obj = json.loads(text)
        except Exception:
            m = re.search(r"\{.*\}", str(text), re.S)
            if not m:
                return FALLBACK
            try:
                obj = json.loads(m.group(0))
            except Exception:
                return FALLBACK
    return {
        "blind_spots": obj.get("blind_spots", []),
        "tradeoffs": obj.get("tradeoffs", {"gains": [], "gives_up": []}),
        "premortem": obj.get("premortem", []),
    }


def handler(event, context):
    # CORS preflight
    method = (event.get("requestContext", {}).get("http", {}) or {}).get("method", "POST")
    if method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS, "body": ""}

    try:
        payload = json.loads(event.get("body") or "{}")

        # 1) start the crew
        started = _http("POST", CREW_URL + "/kickoff", {"inputs": payload})
        kid = started.get("kickoff_id") or started.get("id")
        if not kid:
            return {"statusCode": 200, "headers": CORS, "body": json.dumps(FALLBACK)}

        # 2) poll until it finishes (Lambda timeout should be 2 min)
        result_text = None
        for _ in range(40):  # ~40 * 3s = 2 min
            time.sleep(3)
            st = _http("GET", CREW_URL + "/status/" + str(kid))
            state = str(st.get("state", "")).lower()
            if state in ("success", "completed", "complete", "succeeded"):
                result_text = st.get("result") or st.get("output") or st.get("last_task_output")
                break
            if state in ("failed", "error"):
                break

        if result_text is None:
            return {"statusCode": 200, "headers": CORS, "body": json.dumps(FALLBACK)}

        return {"statusCode": 200, "headers": CORS, "body": json.dumps(_extract_json(result_text))}

    except urllib.error.HTTPError as e:
        return {"statusCode": 200, "headers": CORS, "body": json.dumps(FALLBACK)}
    except Exception as e:
        return {"statusCode": 200, "headers": CORS, "body": json.dumps(FALLBACK)}
