from google import genai
from google.genai import types
from dotenv import load_dotenv

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
        model='gemma-4-26b-a4b-it',
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
        model='gemma-4-26b-a4b-it',
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
        model='gemma-4-26b-a4b-it',
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
        model='gemma-4-26b-a4b-it',
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
def suggest_modification_to_resolve_error(error, code):
    res = client.models.generate_content(
        model='gemma-4-26b-a4b-it',
        contents=f"""
        You are an expert Python developer and code fixer.
        The user provided an existing code snippet and a runtime or syntax error message.
        Analyze the error and modify the code so that the error is resolved.

        Error message:
        {error}

        Original code:
        {code}

        Return strictly valid Python code as a single string in JSON with key `fixed_code`.
        Also include a short `fix_description` (1-2 sentences) that explains what changed.
        """,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "fixed_code": {"type": "STRING"},
                    "fix_description": {"type": "STRING"}
                },
                "required": ["fixed_code", "fix_description"]
            }
        )
    )

    parsed = eval(res.text)
    return {
        "code": parsed.get("fixed_code", code),
        "description": parsed.get("fix_description", "No change made")
    }
def generate_skills(topic):
    with open("skills/skill_template.md","r") as f:
        file = f.read()
    res = client.models.generate_content(
        model='gemma-4-26b-a4b-it',
        contents=[f"""
        You are given with a skill template in the form of a .md file.
        Your job is to generate a skill for the agent for the topic "{topic}" which can be used to complete the task.
        The skill.md must take care of informing the model about the task and how to complete it.(Using programming languages and NOT BUILDING ANOTHER SKILL FILE)
        Generate it in the form of md so that LLMs like you can understand it easily.
        """,file],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "skill": {
                        "type": "STRING"
                    }
                },
                "required": ["skill"]
            }
        )
    )

    with open(f"skills/{topic.replace(' ','_')}_skill.md","w") as f:
        f.write(eval(res.text)['skill'])
    return "Skill generated successfully"

def generate_tasks(skill_file_path: str, task: str):
    with open(skill_file_path, "r") as f:
        skill_content = f.read()
        
    res = client.models.generate_content(
        model='gemma-4-26b-a4b-it',
        contents=[f"""
        You are an expert developer. You are provided with a skill file containing instructions and guidelines, and a specific task to accomplish.
        Your goal is to complete the task by rigorously following the given skill guidelines.
        Determine the necessary terminal commands to run and the files to be created to accomplish this task.
        """, skill_content, f"Task to complete: {task}"],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "commands": {
                        "type": "ARRAY",
                        "items": {
                            "type": "STRING"
                        }
                    },
                    "files_to_be_created": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "file_name": {
                                    "type": "STRING"
                                },
                                "content": {
                                    "type": "STRING"
                                }
                            },
                            "required": ["file_name", "content"]
                        }
                    }
                },
                "required": ["commands", "files_to_be_created"]
            }
        )
    )
    return eval(res.text)

def combine_tool_and_model_res(model_res, tool_res, user_ques,memory_context):
    res = client.models.generate_content(
        model='gemma-4-26b-a4b-it',
        contents=f"""
        You are given with a model response and a tool response.
        User's question: {user_ques}
        Model response: {model_res}
        Tool response: {tool_res}
        Memory Context: {memory_context}
        Step 1 - Extract memory:
        Identify any key facts or personal information about the user present in this conversation
        (e.g. their name, preferences, goals, or any context useful to remember in future turns).
        Store these as concise bullet points in the 'memory' field.
        If there is nothing worth remembering, leave 'memory' as an empty string.

        Step 2 - Build combined_response:
        Using the memory you just extracted (Step 1) as context, combine the model response and tool response
        into a single meaningful, personalised reply to the user's question.
        - Do NOT just concatenate; summarise and make it coherent.
        - Use any relevant facts from memory to make the response feel personalised (e.g. address the user by name if known).
        - Discard any components that are not relevant to the user's question.
        - The 'memory' field must NOT appear verbatim inside 'combined_response'.
        """,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "combined_response": {
                        "type": "STRING"
                    },
                    "memory": {
                        "type": "STRING"
                    }
                },
                "required": ["combined_response", "memory"]
            }
        )
    )
    parsed = eval(res.text)
    return parsed['combined_response'], parsed['memory']

def perform_verification(code,language='python'):
    res = client.models.generate_content(
        model='gemma-4-26b-a4b-it',
        contents=f"""
        You are given with a code in {language}.
        Review the code and fix any errors in the code.
        Code: {code}

        Also list out the additional tasks required if any to complete the user's instruction.
        """,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "modified_code": {
                        "type": "STRING"
                    }
                },
                "required": ["modified_code"]
            }
        )
    )
    return res.text

def generate_steps_prompt(message, agents):
    """
    Generate a list of steps to complete a task, assigning each step to the most suitable agent.

    Args:
        message: The task/message to break into steps.
        agents: A list of dicts, each with 'name' and 'description' keys.
                e.g. [{'name': 'flask-backend', 'description': 'Builds Flask servers'}, ...]
    """
    # Build a readable summary of available agents for the prompt
    agent_summary = "\n".join(
        f"- Agent Name: \"{a['name']}\", Description: \"{a['action']}\""
        for a in agents
    )

    res = client.models.generate_content(
        model='gemma-4-26b-a4b-it',
        contents=f"""
        You are given a task and a list of available agents with their names and descriptions.
        Your job is to break the task into a list of actionable steps to complete it.
        For each step, you MUST assign it to the most suitable agent based on the agent's name and description.
        Only use agents from the provided list.
        Each step_description MUST include the agent name within it, describing both what to do and which agent handles it.
        For example: "Use the flask-backend agent to set up the REST API endpoints for menu items and orders."

        Task: {message}
        Also give a suitable name for the final app
        Available Agents:
        {agent_summary}
        Stick to the same names as mentioned in the available agents list, don't make even a small change in the names.
        """,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "app_name": {
                        "type": "STRING"
                    },
                    "steps": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "step_description": {
                                    "type": "STRING"
                                }
                            },
                            "required": ["step_description"]
                        }
                    }
                },
                "required": ["app_name", "steps"]
            }
        )
    )
    return eval(res.text)
if __name__ == "__main__":
    #code = open("backend-dev/app.py","r").read()
    #print(modify_code(code,"python",["Add a new route to the app which will redirect to the user's linkedin page","Add a new route to the app which will redirect to the user's linkedin page"]))
    #code = format_python_code(code)    
    #with open("backend-dev/app.py","w") as f:
    #    f.write(code['formatted_code'])
    #print(give_info_for_coding_task("You are good at building frontends", "Design a react app which can be used to order food for a restaurant"))
    #print(process_query_to_json("List the agents which build the front end and status active"))
    #print(generate_tasks("skills/developing_flask_servers_skill.md","develop a flask server which can be used to order food for a restaurant"))
    #print(generate_tasks("skills/developing_flask_servers_skill.md","develop a flask server which can be used to order food for a restaurant"))
    #print(perform_verification(open("flask-backend/app.py","r").read()))
    print(generate_steps_prompt("Develop a react app which can be used to order food for a restaurant", [{"name": "flask-backend", "action": "Builds Flask servers"}, {"name": "react-frontend", "action": "Builds React frontends"}]))