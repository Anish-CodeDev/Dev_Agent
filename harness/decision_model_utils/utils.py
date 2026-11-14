# Command to run to spinup model backend: strands-decider serve StrandsAgents/strands-decider-2B-hobson-v19 --port 8080
import requests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from google import genai
from google_api import get_configured_google_api_key
from dotenv import load_dotenv
load_dotenv()

def ask_systemone(state,question=None):
    low = 0.3
    if not question:
        question = ("Does this message ask the assistant to perform a task such as "
        "searching, creating, analyzing, running something, or multi-step work?")
    '''
    url = 'http://host.docker.internal:8080/v1/systemone'
    body = {
        "state":state,
        "questions":{
            "is_task":{"type":"noul","instructions":question}
        }
    }
    '''
    client = genai.Client(api_key=get_configured_google_api_key(),http_options={"api_version": "v1beta"})
    #client = genai.Client(http_options={"api_version": "v1beta"})
    res = client.decisions.create(
        model='gemini-decision-1',
        input=state,
        questions={
             "is_task":{
                 "type":"noul",
                 "instructions":question
            }
        }
    )
    r = res.answers['is_task']
    p = r.noul
    print(f"Score: {p:.2f}, Confidence: {r.confidence:.2f}")
    return p>low

if __name__ == "__main__":
    print(ask_systemone("hey there"))