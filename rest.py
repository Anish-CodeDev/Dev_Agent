import requests
class RestApi:
    def __init__(self,url):
        self.url = url
    
    def post(self,data):
        response = requests.post(self.url,json=data)
        return response.json()
'''
res = RestApi("http://localhost:5000/")
print(res.post({"Question":"print(\"Hey there\")","filename":"agent.py","task":"Build a backend for a website"}))
'''