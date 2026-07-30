import sqlite3
from datetime import datetime

# ---------------------------------------------------------
# 1. INITIALIZE DATABASE
# ---------------------------------------------------------

def init_memory_db():
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            content TEXT,
            importance INTEGER,
            embedding BLOB,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    

def embed_text(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


# ---------------------------------------------------------
# 2. SAVE MEMORY
# ---------------------------------------------------------

def save_memory(memory_type, content, importance=1):
    embedding = embed_text(content)

    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO memory (type, content, importance, embedding)
        VALUES (?, ?, ?, ?)
    """, (memory_type, content, importance, sqlite3.Binary(pickle.dumps(embedding))))

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# 3. RETRIEVE RELEVANT MEMORIES
# ---------------------------------------------------------

import numpy as np
import pickle

def retrieve_memories_semantic(query, limit=5):
    query_embedding = embed_text(query)

    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    cursor.execute("SELECT content, embedding FROM memory")
    rows = cursor.fetchall()
    conn.close()

    scored = []
    for content, emb_blob in rows:
        emb = pickle.loads(emb_blob)
        score = np.dot(query_embedding, emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb))
        scored.append((score, content))

    scored.sort(reverse=True, key=lambda x: x[0])

    return [content for score, content in scored[:limit]]


# ---------------------------------------------------------
# 4. MEMORY EXTRACTION RULES
# ---------------------------------------------------------

def extract_memory_from_user_message(message):
    msg = message.lower()

    # Explicit memory instruction
    if msg.startswith("remember"):
        content = message[8:].strip()
        save_memory("explicit", content, 3)
        return "Okay, I will remember that."

    # Preferences
    if "i like" in msg or "i prefer" in msg:
        save_memory("preference", message, 2)

    # Personal facts
    if "my name is" in msg or "i live in" in msg:
        save_memory("personal_fact", message, 2)

    return None


# ---------------------------------------------------------
# 5. INJECT MEMORY INTO ASSISTANT CONTEXT
# ---------------------------------------------------------

def build_memory_context(user_message):
    memories = retrieve_memories_semantic(user_message)
    if not memories:
        return ""

    return "Relevant memories:\n" + "\n".join(f"- {m}" for m in memories)


from openai import OpenAI
client = OpenAI()

def generate_ai_response(user_message, memory_context):
    system_prompt = f"""
    You are an AI assistant with long-term memory.
    Use the following memories if they are relevant:

    {memory_context}

    Respond helpfully and naturally.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    return response.choices[0].message.content

# ---------------------------------------------------------
# 6. DEMO USAGE
# ---------------------------------------------------------

if __name__ == "__main__":
    init_memory_db()

    print("Memory system ready.\n")

    while True:
        user_input = input("You: ")

        # Extract memory if needed
        memory_response = extract_memory_from_user_message(user_input)
        if memory_response:
            print("AI:", memory_response)
            continue

        # Retrieve relevant memories
        memory_context = build_memory_context(user_input)

        print("\n--- MEMORY CONTEXT ---")
        print(memory_context if memory_context else "(No relevant memories)")
        print("----------------------\n")

        # Here you would normally call your LLM
        ai_reply = generate_ai_response(user_input, memory_context)
        print("AI:", ai_reply, "\n")