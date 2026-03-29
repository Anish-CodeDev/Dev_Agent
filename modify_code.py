from google.genai import Client,types
import os
from dotenv import load_dotenv
from rest import RestApi
load_dotenv()
gemini = Client()


class ModifyCodeFuncs:
    def __init__(self,instruction,folder_name):
        self.instruction = instruction
        self.model = "gemini-3-flash-preview"
        self.folder_name = folder_name
    def generate_summary_for_code(self,filename:str):
        with open(filename,"r") as f:
            code = f.read()
        res = gemini.models.generate_content(
            model=self.model,
            contents=f"""
            You are a code analysis tool.
            Analyze the following code and provide a summary of what it does.
            Code:
            {code}
            """,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "Summary of the code"
                        }
                    },
                    "required": ["summary"]
                }
            )
        )
        return res.text
    def compile_descriptions_of_all_files(self):
        res = []
        rest = RestApi("http://localhost:5000/")
        for filename in os.listdir(self.folder_name):
            if not filename.endswith('.py'):
                continue
            if filename == '.git' or filename == 'agent.py':
                continue
            with open(os.path.join(self.folder_name,filename),"r") as f:
                code = f.read()
            if filename.endswith(".py"):
                if(rest.post({"Question":code,"filename":filename,"task":self.instruction})['res'] == "yes"):
                    print(filename)
                    res.append({"filename":filename,"summary":eval(self.generate_summary_for_code(os.path.join(self.folder_name,filename)))["summary"]})
                    print(res)
        return res
    def generate_task_for_each_file_based_on_summary(self,summary:str):
        res = gemini.models.generate_content(
            model=self.model,
            contents=f"""
            You are a code analysis tool.
            Analyze the following code and provide a task for each file based on the summary with respect to the primary task of the user: {self.instruction}.
            If you feel it has no relevance with respect to the primary task of the user: {self.instruction}, set the task to None
            Code:
            {summary}
            """,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "filename":{
                            "type": "string"
                        },
                        "task":{
                            "type": "string"
                        }
                    },
                    "required": ["filename","task"]
                }
            )
        )
        return res.text
    def generate_final_tasks(self):
        descriptions = self.compile_descriptions_of_all_files()
        res = []
        for description in descriptions:
            r = self.generate_task_for_each_file_based_on_summary(description["summary"])
            if r['task'] != "None":
                res.append(r)
        return res
'''
obj = ModifyCodeFuncs("I want you to add a new feature to the agent.py file which will help in modifying the code")
print(obj.generate_final_tasks())

obj = ModifyCodeFuncs("I want you to add a new feature to the agent.py file which will help in modifying the code")
print(obj.compile_descriptions_of_all_files())
'''