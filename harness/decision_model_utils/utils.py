import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from google_api import get_google_client
from dotenv import load_dotenv
load_dotenv()

def ask_systemone(state,question=None):
    low = 0.3
    if not question:
        question = ("Does this message ask the assistant to perform a task such as "
        "searching, creating, analyzing, running something, or multi-step work?")


    res = get_google_client().decisions.create(
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