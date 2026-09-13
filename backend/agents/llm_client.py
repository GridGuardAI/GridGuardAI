"""
GridGuard AI - Shared LLM client
Wraps whichever LLM API you choose (Gemini, Anthropic Claude, or OpenAI).
Reads API keys from a .env file (project root) or environment variables.

Setup:
    1. Copy .env.example to .env in the project root
    2. Fill in your GEMINI_API_KEY (or ANTHROPIC_API_KEY / OPENAI_API_KEY)
    3. pip install -r requirements.txt
"""

import os
import time
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" | "anthropic" | "openai"

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 20


def call_llm(prompt: str, system: str = "", max_tokens: int = 300) -> str:
    """Send a prompt to the configured LLM and return the text response.
    Retries automatically on rate-limit (429) errors."""
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if PROVIDER == "gemini":
                return _call_gemini(prompt, system, max_tokens)
            elif PROVIDER == "anthropic":
                return _call_anthropic(prompt, system, max_tokens)
            elif PROVIDER == "openai":
                return _call_openai(prompt, system, max_tokens)
            else:
                raise ValueError(f"Unknown LLM_PROVIDER: {PROVIDER}")
        except Exception as e:
            last_error = e
            is_rate_limit = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
            if is_rate_limit and attempt < MAX_RETRIES:
                print(f"[llm_client] Rate limited, retrying in {RETRY_DELAY_SECONDS}s "
                      f"(attempt {attempt}/{MAX_RETRIES})...")
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            raise
    raise last_error


def call_llm_vision(prompt: str, image_bytes: bytes, mime_type: str, system: str = "", max_tokens: int = 500) -> str:
    """Send an image + prompt to the configured LLM (for bill photo/PDF reading).
    Currently implemented for Gemini only (multimodal)."""
    if PROVIDER != "gemini":
        raise NotImplementedError("Vision calls are currently implemented for Gemini only.")
    return _call_gemini_vision(prompt, image_bytes, mime_type, system, max_tokens)


def _call_gemini(prompt, system, max_tokens):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system or "You are an expert electrical engineering assistant.",
            max_output_tokens=max_tokens,
        ),
    )
    return response.text


def _call_gemini_vision(prompt, image_bytes, mime_type, system, max_tokens):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

    response = client.models.generate_content(
        model=model_name,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            prompt,
        ],
        config=types.GenerateContentConfig(
            system_instruction=system or "You extract structured data from documents.",
            max_output_tokens=max_tokens,
        ),
    )
    return response.text


def _call_anthropic(prompt, system, max_tokens):
    import anthropic
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system or "You are an expert electrical engineering assistant.",
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in message.content if hasattr(block, "text"))


def _call_openai(prompt, system, max_tokens):
    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system or "You are an expert electrical engineering assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content
