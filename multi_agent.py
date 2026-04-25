from gemini import generate_steps_prompt,check_sufficiency
from mongodb import DBOps
import os
class MultiAgent:
    def __init__(self,message):
        self.message = message
        self.agents = []
        self.skills = []
    def get_agents(self):
        db = DBOps()
        res = db.find_documents({})
        for agent in res:
            self.agents.append({'name':agent['name'],'action':agent['action']})
    
    def setup(self):
        self.get_agents()
        self.get_skills()
        res = check_sufficiency(self.message, self.agents, self.skills)
        return res
    def get_skills(self):
        for skill in os.listdir("skills"):
            if skill.endswith(".md") and skill != "skill_template.md":
                self.skills.append(skill)
    def generate_steps(self):
        # Consists of the final name of the app and the steps to complete the task(agent name and step description)
        self.get_agents()
        res = generate_steps_prompt(self.message,self.agents)
        return res

if __name__ == "__main__":
    multi_agent = MultiAgent("Create a food ordering app and a web page for it using vanilla css and vanilla js")
    #print(multi_agent.get_agents())
    multi_agent.get_skills()
    print(multi_agent.setup())
    print(multi_agent.generate_steps())