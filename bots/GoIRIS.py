#IRIS
import requests
import json

apihead={"Content-Type":"application/json;charset=utf-8"}
#url="http://ec2-35-77-33-129.ap-northeast-1.compute.amazonaws.com/production/request"
#url="http://localhost:52774/production/request"
#url="https://ubuntu-iris1.japaneast.cloudapp.azure.com/production/request"
#url="https://ubuntu1.japaneast.cloudapp.azure.com/production/request"
url="https://20.222.203.150/production/request"
def post_iris(payload):
    ret = requests.post(url,headers=apihead,data=payload,verify=False)
    return ret.json()

def get_iris(param):
    geturl = url + "/" + param
    ret = requests.get(geturl,headers=apihead,verify=False)
    return ret.json()