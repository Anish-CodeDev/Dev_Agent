from distro import name
from google import genai
from google.genai import types
from dotenv import load_dotenv
from typing_extensions import TypedDict,Optional
import typing

load_dotenv()

client = genai.Client()

def process_query_to_json(query: str):
    # Precise instructions for the 'one-key-per-object' array format
    sys_instr = (
        "Convert the natural language query into a JSON database filter. "
        "The output must be a single object with the key '$or'. "
        "The value of '$or' must be an array of objects, where EACH object contains "
        "exactly ONE key (either 'name', 'action', or 'status'). "
        "Example: {'$or': [{'name': 'John'}, {'status': 'active'}]} "
        "If a field is missing, do not include an object for it."
    )

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=f"Query: {query}",
        config=types.GenerateContentConfig(
            system_instruction=sys_instr,
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "$or": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "name": {
                                    "type": "STRING",
                                    "nullable":True
                                },
                                "action": {
                                    "type": "STRING",
                                    "nullable":True
                                },
                                "status": {
                                    "type": "STRING",
                                    "nullable":True
                                }
                            }
                        }
                    }
                },
                "required": ["$or"]
            }
        )
    )
    return eval(response.text)


def give_info_for_coding_task(sys_instr:str,query:str):
    res = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=f"""
        You are given with a task to complete: {query}
        
        You have to do the following:
        1. List out the packages required to complete the task.
        2. Give me the number of files required to complete the task.
        3. Give me the code for each file in the task.
        4. Without fail the mention the core framework used
        5. Don't missout on the code for any file.
        """,
        config=types.GenerateContentConfig(
            system_instruction=sys_instr,
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "language": {
                        "type": "STRING"
                    },
                    "packages": {
                        "type": "ARRAY",
                        "items": {
                            "type": "STRING"
                        }
                    },
                    "prerequisite_commands_to_run": {
                        "type": "ARRAY",
                        "items": {
                            "type": "STRING"
                        }
                    },
                    "files": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "file_name": {
                                    "type": "STRING"
                                },
                                "code": {
                                    "type": "STRING"
                                }
                            }
                        }
                    },
                    "file_to_be_executed": {
                        "type": "STRING"
                    },
                    "main_frameword_used":{
                        "type": "STRING"
                    }
                },
                "required": ["packages", "files","file_to_be_executed","main_frameword_used","prerequisite_commands_to_run"]
            }
        )
    )
    return eval(res.text)

def format_python_code(code,language):
    res = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=[
            f"""
            You are given with a code in {language}, you have to format the code in a way that it is easy to read and understand.
            Also review the code and fix any errors in the code.
            Code: {code}
            """
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "formatted_code": {
                        "type": "STRING"
                    }
                },
                "required": ["formatted_code"]
            }
        )
    )
    return eval(res.text)

code = 'from flask import Flask, render_template, request\napp = Flask(__name__)\n@app.route("/", methods=["GET", "POST"]):\ndef index():\n    if request.method == "POST":\n        return f"Form submitted! Name: {request.form.get("name")}"\n    return render_template("index.html")\nif __name__ == "__main__":\n    app.run()'

def modify_code(code,language,instruction):
    res = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=f"""
        You are given with a code in {language}, you have to modify the code in a way that it is easy to read and understand according to the user's instruction.
        Also review the code and fix any errors in the code.
        Code: {code}
        Instruction: {instruction}

        Also list out the additional tasks required if any to complete the user's instruction.
        """,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "modified_code": {
                        "type": "STRING"
                    },
                    "additional_tasks":{
                        "type":"ARRAY",
                        "items":{
                            "type":"STRING"
                        }
                    }
                },
                "required": ["modified_code","additional_tasks"]
            }
        )
    )
    return {"code":format_python_code(res.text,language)['formatted_code'],"additional_tasks":eval(res.text)['additional_tasks']}
#code = open("backend-dev/app.py","r").read()
#print(modify_code(code,"python",["Add a new route to the app which will redirect to the user's linkedin page","Add a new route to the app which will redirect to the user's linkedin page"]))
#code = format_python_code(code)    
#with open("backend-dev/app.py","w") as f:
#    f.write(code['formatted_code'])
#print(give_info_for_coding_task("You are good at building frontends", "Design a react app which can be used to order food for a restaurant"))
#print(process_query_to_json("List the agents which build the front end and status active"))