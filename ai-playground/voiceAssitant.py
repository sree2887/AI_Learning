import sounddevice as sd
from scipy.io.wavfile import write
from openai import OpenAI
import subprocess
import os
import json

client = OpenAI()

# ---------------------------
# MEMORY SYSTEM
# ---------------------------

MEMORY_FILE = "memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

def update_memory(user_text, memory):
    text = user_text.lower()

    # Learn user's name
    if "my name is" in text:
        name = user_text.split("is")[-1].strip()
        memory["name"] = name
        save_memory(memory)
        return f"Got it. I’ll remember your name is {name}."

    # Learn user's likes
    if "i like" in text:
        item = user_text.split("like")[-1].strip()
        memory.setdefault("likes", []).append(item)
        save_memory(memory)
        return f"Okay, I’ll remember that you like {item}."

    return None

# ---------------------------
# RECORD AUDIO
# ---------------------------

def record_audio(duration=5, filename="input.wav"):
    print("\n🎤 Recording... Speak now.")
    fs = 44100
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    write(filename, fs, audio)
    print("✔ Recording complete.")
    return filename

# ---------------------------
# TRANSCRIBE AUDIO
# ---------------------------

def transcribe_audio(file_path):
    with open(file_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=f
        )
    return response.text

# ---------------------------
# AI REPLY WITH MEMORY
# ---------------------------

conversation_history = []
memory = load_memory()

def get_ai_reply(text):
    # Check if user said something to remember
    memory_reply = update_memory(text, memory)
    if memory_reply:
        return memory_reply

    conversation_history.append({"role": "user", "content": text})

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "system",
                "content": f"""
                You are a friendly, calm voice assistant.
                You explain things clearly and simply.
                Here is what you know about the user:
                {json.dumps(memory, indent=2)}
                """
            },
            *conversation_history
        ]
    )

    reply = response.output_text
    conversation_history.append({"role": "assistant", "content": reply})

    return reply

# ---------------------------
# SPEAK USING OPENAI TTS
# ---------------------------

def speak(text, filename="reply.wav"):
    print("Generating speech...")

    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text
    )

    audio_bytes = response.read()

    with open(filename, "wb") as f:
        f.write(audio_bytes)

    print("Saved audio file:", os.path.abspath(filename))
    subprocess.run(["cmd", "/c", "start", "/min", filename])

# ---------------------------
# MAIN LOOP
# ---------------------------

if __name__ == "__main__":
    print("🎧 Voice Assistant Ready")
    print("Press Enter to talk. Type 'exit' to quit.\n")

    while True:
        command = input("Press Enter to speak... ")

        if command.lower() == "exit":
            print("Goodbye!")
            break

        audio_file = record_audio()
        text = transcribe_audio(audio_file)
        print("You said:", text)

        reply = get_ai_reply(text)
        print("AI:", reply)

        speak(reply)