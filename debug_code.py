from google import genai
from google.genai import types
from dotenv import load_dotenv
from gemini import suggest_modification_to_resolve_error

load_dotenv()
gemini = genai.Client()

class Debug:
    def __init__(self,error):
        self.error = error
        self.model = 'gemini-3-flash-preview'
        
    def extract_file(self):
        res = gemini.models.generate_content(
            model=self.model,
            contents=[
                f"""
                You have been given with an error messages: {self.error}, your job is to return the name of the files due to which the error has been caused.
                You will not return filenames of files part of libraries, you can only return the files which were written by the agent or the user.

                """
            ],
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema={
                    "type":"object",
                    "properties":{
                        "filenames":{
                            "type":"ARRAY",
                            "items":{
                                "type":"STRING"
                            }
                        },
                        "error":{
                            "type":"STRING"
                        }
                    },
                    "required": ["filenames","error"]
                }
            )          
        )
        return eval(res.text)['filenames']
    def reveal_code(self,path):
        code = ''
        with open(path,'r') as f:
            code = f.read()
        return code
    
    def suggest_changes(self,paths):
        for path in paths:
            code = self.reveal_code(path)
            res = suggest_modification_to_resolve_error(self.error,code)
            print("Here is the change suggested: Press Y or N")
            print(res['code'])
            inp = input("Y/N: ")
            if(inp == 'Y'):
                with open(path,'w') as f:
                    f.write(res['code'])
            else:
                print("Change Skipped")
        return "Changes were updated as per your wish"

obj = Debug(r"""
Traceback (most recent call last):
  File "C:\Anish\Computer_Science\AI\Agentic AI\Projects\dev_agent\test.py", line 1, in <module>
    foiwjfoerfhorefh
NameError: name 'foiwjfoerfhorefh' is not defined
""")
print(obj.suggest_changes(obj.extract_file()))