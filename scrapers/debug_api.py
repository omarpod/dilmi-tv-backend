import requests
import json

url = "https://www.scorebat.com/video-api/v3/"
response = requests.get(url)
data = response.json()

# طباعة أول مباراة لنرى هيكلها
print(json.dumps(data['response'][0], indent=4))