from langgraph.graph import StateGraph,START,END
from langchain_core.messages import BaseMessage,SystemMessage,HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Annotated,Sequence,TypedDict
from dotenv import load_dotenv
from mongodb import DBOps
from gemini import process_query_to_json,give_info_for_coding_task,format_python_code
import os
from code_gen import install_packages
from pathlib import Path
load_dotenv()
db = DBOps()
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
def modify_agent(name:str):
    """
    This tool is used to modify an agent(edit and delete)
    ARGS: name
    """
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
        for r in res:
            print("System Prompt: ",r['action'])
            print("User's request: ",task)

        info = give_info_for_coding_task(r['action'],task)
        folder_name = name
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        if info['language'] == "javascript":
            print("Came till here")
            if install_packages(info['packages'],"javascript",folder_name):
                if 'react' in info['main_frameword_used'] or 'React' in info['main_frameword_used']:

                    for file in info['files']:
                        with open(f"{folder_name}/{file['file_name'].replace('.js','.jsx')}","w") as f:
                            f.write(file['code'])

                    
                        os.system(f"cd {folder_name} && npm install vite @vitejs/plugin-react -D")
                        with open(f"{folder_name}/vite.config.js","a") as f:
                            
                            f.write("""import { defineConfig } from 'vite';
                                    import react from '@vitejs/plugin-react';

                                    // https://vitejs.dev/config/
                                    export default defineConfig({
                                    plugins: [react()],
                                    server: {
                                        port: 3000, // Optional: sets the port to 3000
                                    },
                                    });
                                    """)

                        with open(f"{folder_name}/package.json","a") as f:
                            f.write("""{
                                    "scripts": {
                                        "dev": "vite",
                                        "build": "vite build",
                                        "preview": "vite preview"
                                    }
                                    }""")
                        with open(f"{folder_name}/index.html","w") as f:
                            f.write(f"""<!doctype html>
                                    <html lang="en">
                                    <head>
                                        <meta charset="UTF-8" />
                                        <link rel="icon" type="image/svg+xml" href="/vite.svg" />
                                        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                                        <title>{folder_name}</title>
                                    </head>
                                    <body>
                                        <div id="root"></div>
                                        <script type="module" src="/src/{info['file_to_be_executed']}"></script>
                                    </body>
                                    </html>
                                    """)
                  
                 

                else:

                    for file in info['files']:
                        with open(f"{folder_name}/{file['file_name']}","w") as f:
                            f.write(file['code'])
                return "Agent has completed it's task"   

            else:
                return "Packages not installed"
        
        elif info['language'] == "python":
            if install_packages(info['packages'],"python",folder_name):
                for file in info['files']:
                    with open(f"{folder_name}/{file['file_name']}","w") as f:
                        try:
                            path = Path(file['file_name'])
                            if not os.path.exists(path.parent):
                                os.makedirs(path.parent)
                            if file['file_name'].endswith('.py'):
                                f.write(format_python_code(file['code'],info['language'])['formatted_code'])
                            else:
                                f.write(file['code'])
                        except Exception as e:
                            print(e)
                            return "An error occurred while creating the files"
                return "Agent has completed it's task"   
            else:
                return "Packages not installed"
        
        else:
            for file in info['files']:
                with open(f'{folder_name}/{file["file_name"]}','w') as f:
                    path = Path(file['file_name'])
                    if not os.path.exists(path.parent):
                        os.makedirs(path.parent)
                    f.write(format_python_code(file['code'],info['language'])['formatted_code'])
    else:
        print("Agent not found")
        return "Agent not found"
@tool
def modify_code_tool(instruction:str):
    """
    This tool is used to modify the code
    ARGS: instruction
    """
    return f"Your {instruction} was to modify the file."
tools = [create_agent,view_agent,modify_agent,assign_task_to_agent]

llm = ChatGoogleGenerativeAI(model='gemini-3-flash-preview').bind_tools(tools)


def agent(state:AgentState):

    instruction = SystemMessage(content="You are a helpful assistant, answer to your best ability")
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
    res = app.invoke({'messages':conversational_history})
    conversational_history = res['messages']
    print(res['messages'][1].content[0]['text'])
    user_inp = input("Enter something: ")