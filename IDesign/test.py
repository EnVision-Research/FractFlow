import requests
import json
url = "https://gpt-api.hkust-gz.edu.cn/v1/chat/completions"
headers = { 
"Content-Type": "application/json", 
"Authorization": "cap3d 58d0bacc761d4678855f9582819abcc77a4bacaa54984213905d9d546670638a" #Please change your KEY. If your key is XXX, the Authorization is "Authorization": "Bearer XXX"
}
data = { 
"model": "gpt-4o-2024-08-06", # # "gpt-3.5-turbo" version in gpt-4o-mini, "gpt-4" version in gpt-4o-2024-08-06
"messages": [{"role": "user", "content": "who are you. don't think. give your answer as soon as possible"}], 
"temperature": 0.7 
}
response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json())
# DeepSeek API配置

