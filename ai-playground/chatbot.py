from openai import OpenAI
import json
import os

def load_memory():
    if os.path.exists("memory.json"):
        with open("memory.json", "r") as f:
            return json.load(f)
    return {}

def save_memory(memory):
    with open("memory.json", "w") as f:
        json.dump(memory, f, indent=4)


client = OpenAI()
memory = load_memory()

print("AI Chatbot with memory is ready. Type 'exit' to quit.\n")

conversation = []  # store past messages
conversation = [
    {
        "role": "system",
        "content": (
            "You are a friendly AI tutor. "
            "You explain things simply and clearly. "
            "Here is what you know about the user: " + json.dumps(memory)
        )
    }
]

while True:
    user_input = input("You: ")

    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    if "my name is" in user_input.lower():
        name = user_input.split("is")[-1].strip().rstrip(".")
        memory["name"] = name
        save_memory(memory)

    # Add user message to conversation
    conversation.append({"role": "user", "content": user_input})

    response = client.responses.create(
        model="gpt-4o-mini",
        input=conversation
    )

    ai_reply = response.output_text

    # Add AI reply to conversation
    conversation.append({"role": "assistant", "content": ai_reply})

    print("AI:", ai_reply, "\n")