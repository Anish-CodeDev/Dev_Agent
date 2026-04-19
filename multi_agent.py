from gemini import generate_steps_prompt
from mongodb import DBOps

class MultiAgent:
    def __init__(self,message):
        self.message = message
        self.agents = []
    
    def get_agents(self):
        db = DBOps()
        res = db.find_documents({})
        for agent in res:
            self.agents.append({'name':agent['name'],'action':agent['action']})
    
    def generate_steps(self):
        # Consists of the final name of the app and the steps to complete the task(agent name and step description)
        self.get_agents()
        res = generate_steps_prompt(self.message,self.agents)
        return res

if __name__ == "__main__":
    multi_agent = MultiAgent("Create a food ordering app")
    #print(multi_agent.get_agents())
    print(multi_agent.generate_steps())