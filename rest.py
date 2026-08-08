import requests
class RestApi:
    def __init__(self,url):
        self.url = url
    
    def post(self,data):
        response = requests.post(self.url,json=data)
        return response.json()

if __name__ == "__main__":
    res = RestApi("http://localhost:5000/")
    data = {
        "files":["a.py","b.c"],
        "contents":["abc","cde"],
        "app_name":"test"
    }
    print(res.post(data))
