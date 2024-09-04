from ollama import Client
import pprint

host = "http://localhost:8080"

client = Client(host=host, api_key="1234", api_secret="5678")

messages = [
    {
        "role": "user",
        "content": "Why is the sky blue?",
    },
]

response = client.chat("llama3.1:8b", messages=messages)
pprint.pprint(response)
