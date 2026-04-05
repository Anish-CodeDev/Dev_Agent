from langgraph.graph import StateGraph,START,END
from langchain_core.messages import BaseMessage,SystemMessage,HumanMessage,AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Annotated,Sequence,TypedDict
from dotenv import load_dotenv
from mongodb import DBOps
from gemini import process_query_to_json,give_info_for_coding_task,format_python_code,generate_skills,generate_tasks
import os
from code_gen import install_packages,ModifyCode
from pathlib import Path
from modify_code import ModifyCodeFuncs
from debug_code import Debug
from cli import CLI
from pathlib import Path
from google import genai
from agent_viewer import main
from gemini import combine_tool_and_model_res
load_dotenv()
client = genai.Client()
db = DBOps() 
tool_info = ''
memory_context = '' 
class AgentState(TypedDict):
    messages:Annotated[Sequence[BaseMessage],add_messages]


def should_continue(state:AgentState):
    if state['messages'][-1].tool_calls:
        return "continue"
    else:
        return "end"
graph = StateGraph(AgentState)


@tool
def create_agent(name:str,action:str):
    """
    This tool is used to create an agent
    ARGS: name,action
    """
    if db.check_if_agent_exists(name):
        return f"Agent {name} already exists"
    else:
        res = db.insert_document({'name':name,'action':action,'status':'inactive'})
        print(res)
        return f"Agent {name} created with action {action}" 

@tool
def view_agent(query:str):
    """
    This tool is used to view all the agents created by the user.
    DO NOT USE THIS TOOL IN THE USER WANTS TO CHANGE THE DESCRIPTION, NAME OR DELETE THE AGENT.
    ARGS: query
    """
    #res = db.find_all_documents(query)
    #print(res)
    query = process_query_to_json(query)
    res = db.find_documents(query)
    if res:
        for r in res:
            print("Name: ",r['name'])
            print("Action: ",r['action'])
            print("Status: ",r['status'])
            print("----------------")
    return f"Agents were shown"
@tool
def modify_agent():
    """
    Opens a dialog box for managing sub-agents. Use this tool when the user wants to:
    - View existing agents
    - Rename an agent
    - Change an agent's description
    - Delete an agent

    Use this tool regardless of whether the user specifies which agent to modify or not.
    DO NOT use any other tool for these operations.
    """
    print("A dialogue box will pop up, please select the agent you want to modify there")
    main()
    print("Test")
    global tool_info
    tool_info = "Interface will pop up.\n"
    return "Interface will pop up"

@tool
def assign_task_to_agent(name:str,task:str):
    """
    This tool is used to assign a task to an agent
    ARGS: name,task
    """
    res = db.find_documents({'name':name})
    if res:
        db.update_document({'name':name},{'$set':{'status':'active'}})
        r = res[0]
        print("System Prompt: ",r['action'])
        print("User's request: ",task)
        print("Agent name: ",name)
        #info = give_info_for_coding_task(r['action'],task)
        folder_name = name
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        # Search for the best skill to solve the user's task
        skills = []
        for skill in os.listdir("skills"):
            if skill.endswith(".md") and skill!="skill_template.md":
                skills.append(skill)
        print('came till here')
        print(skills)
        print("Going into res")
        res = client.models.generate_content(
            model="gemma-4-26b-a4b-it",
            contents=f"""
            You are given a list of skills: {skills}
            You are also given a task: {task}
            Your task is to choose the best skill to solve the user's task
            Return the name of the skill
            """,
            config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "skill": {
                            "type": "string"
                        }
                    },
                    "required": ["skill"]
                }
            }
        )
        skill = eval(res.text)['skill']
        print("skill used",skill)
        # Utilize the chosen skill to generate the code
        res = generate_tasks(f"skills/{skill}",task)
        commands = res['commands']
        print("Installing packages")
        for command in commands:
            cli = CLI(command)
            cli.run_command()
        files_to_modify = res['files_to_be_created']
        print("Creating files and writing code")
        for file in files_to_modify:
            path = Path(folder_name)
            path.mkdir(parents=True, exist_ok=True)
            with open(folder_name+'/'+file['file_name'],'w') as f:
                f.write(file['content'])
    else:
        return "Task not assigned to agent because agent wasn't found"
    db.update_document({'name':name},{'$set':{'status':'inactive'}})
    global tool_info
    tool_info = "Task assigned to agent"
    return "Task assigned to agent"
            
@tool
def modify_code_tool(name:str,instruction:str):
    """
    This tool is used to modify the code
    ARGS: name,instruction
    """
    res = db.find_documents({'name':name})
    if res:
        db.update_document({'name':name},{'$set':{'status':'active'}})
        for r in res:
            system_prompt = r['action']
    
    system_prompt += instruction
    obj = ModifyCodeFuncs(system_prompt,name)
    res = obj.generate_final_tasks()
    
    for r in res:
        with open(r['filename'],'r') as f:
            code = f.read()
        modify_obj = ModifyCode('python',r['task'])
        code = modify_obj.modify_code_gen(code)
        with open(r['filename'],'w') as f:
            f.write(code)    
    db.update_document({'name':name},{'$set':{'status':'inactive'}})
    return f"Your {instruction} was to modify the code base has been completed"

@tool
def debug_code(name:str,error:str):
    """
    This tool is used when the user wants to debug the errors of the code generated by the agent

    ARGS: name, error
    """
    res = db.find_documents({"name":name})
    if res:
        db.update_document({'name':name},{'$set':{'status':'active'}})
    obj = Debug(error)
    res = obj.suggest_changes(obj.extract_file())
    db.update_document({'name':name},{'$set':{'status':'inactive'}})
    return "The changes were updated as per your wish"
@tool
def gen_skills(topic:str):
    """
    This tool is used to generate skills for the agent
    ARGS: topic
    """
    res = generate_skills(topic)
    return res
tools = [create_agent,modify_agent,assign_task_to_agent,modify_code_tool,debug_code,gen_skills]

llm = ChatGoogleGenerativeAI(model='gemma-4-26b-a4b-it').bind_tools(tools)


def agent(state:AgentState):
    global memory_context
    memory_note = f"\n\nThe following are key facts you remember about the user from previous turns:\n{memory_context}" if memory_context else ""
    instruction = SystemMessage(content=f"You are a helpful assistant, answer to your best ability. When a tool returns a message, relay that exact message to the user as your final response. Do not add any additional information.{memory_note}")
    res = llm.invoke([instruction]+state['messages'])
    
    return {'messages':[res]}
graph.add_node('agent',agent)
tool_node = ToolNode(tools=tools)
graph.add_node('tool_node',tool_node)
graph.add_edge(START,'agent')
graph.add_conditional_edges(
    'agent',
    should_continue,

    {
    'continue':'tool_node',
    'end':END
    
    })
graph.add_edge('tool_node','agent')
app = graph.compile()

user_inp = input("Enter something: ")
conversational_history = []

while user_inp!='exit':
    conversational_history.append(HumanMessage(content=user_inp))
    res = app.invoke({"messages":conversational_history})
    #conversational_history = res['messages']
    #print(res)
    model_response = ''
    try:
        if(res['messages'][1].content[1]['text']):
            model_response = res['messages'][1].content[1]['text']
    except:
        pass
    final_res, memory = combine_tool_and_model_res(model_response,tool_info,user_inp,memory_context)
    if memory:
        memory_context += memory + '\n'
    print(memory_context)
    conversational_history.append(AIMessage(content=model_response))
    tool_info = ''
    print("AI: ",final_res)
    user_inp = input("Enter something: ")