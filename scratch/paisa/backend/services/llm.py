import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Multi-provider fallback pattern as defined in execution prompt
PROVIDERS = [
    {
        "name": "groq",       
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",  
        "key": os.getenv("GROQ_API_KEY", "").strip() or None
    },
    {
        "name": "mistral",    
        "base_url": "https://api.mistral.ai/v1",
        "model": "mistral-small-latest",      
        "key": os.getenv("MISTRAL_API_KEY")
    },
    {
        "name": "openrouter", 
        "base_url": "https://openrouter.ai/api/v1",
        "model": "meta-llama/llama-3.1-8b-instruct:free", 
        "key": os.getenv("OPENROUTER_API_KEY")
    },
]

async def call_llm(prompt: str) -> str:
    """Send a prompt to the primary LLM, falling back to others if it fails."""
    for provider in PROVIDERS:
        if not provider["key"]:
            continue
            
        try:
            client = AsyncOpenAI(
                api_key=provider["key"],
                base_url=provider["base_url"]
            )
            response = await client.chat.completions.create(
                model=provider["model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.0
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Provider {provider['name']} failed: {e}")
            continue  # try next provider
            
    # If all fail, return a simulated fallback for local development without API keys
    print("All LLM providers exhausted or no keys provided. Returning mock response.")
    return json.dumps({
        "intent": "query",
        "question": "Local fallback mode without API keys.",
        "answer": "Please set your API keys in the .env file to enable the actual LLM."
    })
