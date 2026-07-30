# pip install requests
import requests, json

def ask_ollama(prompt: str, model: str = "llama3.2") -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False}
    )
    return response.json()["response"]

# Try it
answer = ask_ollama("What is Apache Airflow used for?")
print(answer)