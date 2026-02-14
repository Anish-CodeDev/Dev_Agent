import os
from gemini import modify_code
def install_packages(packages,language,folder_name,prerequisite_commands=''):

    try:
        for package in packages:

            if language == "javascript":
                os.system(f"cd {folder_name} && npm install {package}")
            
            elif language == "python":
                os.system(f"cd {folder_name} && pip install {package}")
        
        for command in prerequisite_commands:
            os.system(f"cd {folder_name} && {command}")
        return True
    except Exception as e:
        print(e)
        return False

class ModifyCode:
    def __init__(self,code,language,instruction):
        self.code = code
        self.language = language
        self.instruction = instruction
    
    def modify_code_gen(self):
        try:
            res = modify_code(self.code,self.language,self.instruction)
            if res['additional_tasks']:
                res = modify_code(res['code'],self.language,res['additional_tasks'])
            return res['code']
        except Exception as e:
            print(e)
            return False

