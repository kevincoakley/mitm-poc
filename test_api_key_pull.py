from ollama import Client
import pprint

host = "http://localhost:8080"

client = Client(host=host, api_key="1234")

response = client.pull("llama3.1:8b")

pprint.pprint(response)
