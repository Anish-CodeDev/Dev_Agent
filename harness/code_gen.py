from gemini import modify_code

class ModifyCode:
    def __init__(self,language,instruction):
        self.language = language
        self.instruction = instruction
        
    def modify_code_gen(self,code):
        try:
            res = modify_code(code,self.language,self.instruction)
            if res['additional_tasks']:
                res = modify_code(res['code'],self.language,res['additional_tasks'])
            return res['code']
        except Exception as e:
            print(e)
            return False

