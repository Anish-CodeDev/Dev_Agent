from google.genai import Client,types
import os
from dotenv import load_dotenv
load_dotenv()
gemini = Client()


class ModifyCode:
    def __init__(self,instruction):
        self.instruction = instruction
        self.model = "gemini-3-flash-preview"
    
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
obj = ModifyCode("You are a code analysis tool")
print(obj.generate_summary_for_code("modify_code.py"))