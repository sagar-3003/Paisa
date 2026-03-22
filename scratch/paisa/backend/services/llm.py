import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

PROVIDERS = [
    {
        "name": "groq",
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
        "key": os.getenv("GROQ_API_KEY", "").strip() or None,
    },
    {
        "name": "mistral",
        "base_url": "https://api.mistral.ai/v1",
        "model": "mistral-small-latest",
        "key": os.getenv("MISTRAL_API_KEY"),
    },
    {
        "name": "openrouter",
        "base_url": "https://openrouter.ai/api/v1",
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "key": os.getenv("OPENROUTER_API_KEY"),
    },
]

# Vision-capable providers (image + text input)
VISION_PROVIDERS = [
    {
        "name": "groq-vision",
        "base_url": "https://api.groq.com/openai/v1",
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "key": os.getenv("GROQ_API_KEY", "").strip() or None,
    },
    {
        "name": "openrouter-vision",
        "base_url": "https://openrouter.ai/api/v1",
        "model": "google/gemini-flash-1.5-8b",
        "key": os.getenv("OPENROUTER_API_KEY"),
    },
]

async def call_llm(prompt: str) -> str:
    """Send a prompt to the primary LLM, falling back to others if it fails."""
    for provider in PROVIDERS:
        if not provider["key"]:
            continue
        try:
            client = AsyncOpenAI(api_key=provider["key"], base_url=provider["base_url"])
            response = await client.chat.completions.create(
                model=provider["model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.0,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Provider {provider['name']} failed: {e}")
            continue

    print("All LLM providers exhausted. Returning mock response.")
    return json.dumps({
        "intent": "query",
        "question": "Local fallback mode without API keys.",
        "answer": "Please set your API keys in the .env file to enable the actual LLM.",
    })

async def call_llm_vision(prompt: str, image_b64: str, mime_type: str = "image/jpeg") -> str:
    """
    Send a prompt + base64-encoded image to a vision-capable LLM.
    Falls back across VISION_PROVIDERS, then falls back to text-only call_llm with a note.
    """
    for provider in VISION_PROVIDERS:
        if not provider["key"]:
            continue
        try:
            client = AsyncOpenAI(api_key=provider["key"], base_url=provider["base_url"])
            response = await client.chat.completions.create(
                model=provider["model"],
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{image_b64}"},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }],
                max_tokens=1500,
                temperature=0.0,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Vision provider {provider['name']} failed: {e}")
            continue

    # Fallback: ask text LLM to do its best without the image
    print("All vision providers exhausted. Falling back to text-only LLM.")
    return await call_llm(
        prompt + "\n\n(Note: image could not be processed — please extract what you can from context.)"
    )
