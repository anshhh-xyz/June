from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROQ_API1"))

def ask_groq(messages,  model="openai/gpt-oss-120b"):
    response = client.chat.completions.create(
        messages=messages,
        model=model
    )
    return response.choices[0].message.content