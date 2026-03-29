# llm_config.py
# Groq API — fast inference, generous free tier
# Best free model: llama-3.3-70b-versatile
# Get your free API key at: https://console.groq.com

import os
from crewai import LLM

def get_llm():
    return LLM(
        model="groq/llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.3,
        max_tokens=1024,
    )
