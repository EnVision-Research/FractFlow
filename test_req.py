import requests

response = requests.post(
    'http://10.30.58.120:50018/api/agents/weatheragent',
    json="{'query': 'Weather in New York'}"
)

result = response.json()
print(result)