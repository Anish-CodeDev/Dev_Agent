# Command to run to spinup model backend: strands-decider serve StrandsAgents/strands-decider-2B-hobson-v19 --port 8080
import requests

def ask_systemone(state,question,low):
    url = 'http://localhost:8080/v1/systemone'
    body = {
        "state":state,
        "questions":{
            "is_task":{"type":"noul","instructions":question}
        }
    }
    r = requests.post(url,json=body)
    p = r.json()['answers']['is_task']['noul']
    print("Score:",p)
    return p>low

if __name__ == "__main__":
    print(ask_systemone("hey there",("Does this message ask the assistant to perform a task such as "
    "searching, creating, analyzing, running something, or multi-step work?"),0.3))