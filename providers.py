"""
Unified vision LLM provider interface.

Supported providers:
  1.  anthropic   — Claude (claude-sonnet-4-6, etc.)
  2.  openai      — GPT-4o, GPT-4-turbo-vision
  3.  gemini      — Gemini 1.5 Pro / Flash (Google)
  4.  groq        — Llama 3.2 Vision (fastest inference)
  5.  mistral     — Pixtral 12B
  6.  together    — Llama / Qwen vision models
  7.  ollama      — Local models (llava, bakllava, etc.)
  8.  azure       — Azure OpenAI (GPT-4V deployment)
  9.  deepseek    — DeepSeek VL2
  10. cohere      — Command R+ (text only, no vision)
"""

from __future__ import annotations
import base64
import json
import os
import re


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

PROVIDERS: dict[str, dict] = {
    "anthropic": {
        "name": "Anthropic",
        "default_model": "claude-sonnet-4-6",
        "vision": True,
        "env_key": "ANTHROPIC_API_KEY",
        "install": "anthropic",
    },
    "openai": {
        "name": "OpenAI",
        "default_model": "gpt-4o",
        "vision": True,
        "env_key": "OPENAI_API_KEY",
        "install": "openai",
    },
    "gemini": {
        "name": "Google Gemini",
        "default_model": "gemini-1.5-pro",
        "vision": True,
        "env_key": "GEMINI_API_KEY",
        "install": "google-generativeai",
    },
    "groq": {
        "name": "Groq",
        "default_model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "vision": True,
        "env_key": "GROQ_API_KEY",
        "install": "groq",
    },
    "mistral": {
        "name": "Mistral AI",
        "default_model": "pixtral-12b-2409",
        "vision": True,
        "env_key": "MISTRAL_API_KEY",
        "install": "mistralai",
    },
    "together": {
        "name": "Together AI",
        "default_model": "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
        "vision": True,
        "env_key": "TOGETHER_API_KEY",
        "install": "together",
    },
    "ollama": {
        "name": "Ollama (local)",
        "default_model": "llava",
        "vision": True,
        "env_key": None,
        "install": "pip install ollama  OR  https://ollama.com",
        "base_url": "http://localhost:11434/v1",
        "note": "Run: ollama pull llava  (or llama3.2-vision, gemma3, mistral, etc.)",
    },
    "lmstudio": {
        "name": "LM Studio (local)",
        "default_model": "local-model",
        "vision": True,
        "env_key": None,
        "install": "https://lmstudio.ai",
        "base_url": "http://localhost:1234/v1",
        "note": "Start LM Studio → Local Server, load any vision model (LLaVA, Gemma, Mistral...)",
    },
    "llamacpp": {
        "name": "llama.cpp server (local)",
        "default_model": "local-model",
        "vision": True,
        "env_key": None,
        "install": "https://github.com/ggerganov/llama.cpp",
        "base_url": "http://localhost:8080/v1",
        "note": "Run: ./server -m model.gguf --mmproj mmproj.gguf -ngl 99",
    },
    "azure": {
        "name": "Azure OpenAI",
        "default_model": "gpt-4o",
        "vision": True,
        "env_key": "AZURE_OPENAI_API_KEY",
        "install": "openai",
        "extra_env": ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_VERSION"],
    },
    "deepseek": {
        "name": "DeepSeek",
        "default_model": "deepseek-chat",
        "vision": False,
        "env_key": "DEEPSEEK_API_KEY",
        "install": "openai",
        "base_url": "https://api.deepseek.com",
        "note": "Vision not yet available on DeepSeek API — uses text description of screen",
    },
    "cohere": {
        "name": "Cohere",
        "default_model": "command-r-plus",
        "vision": False,
        "env_key": "COHERE_API_KEY",
        "install": "cohere",
        "note": "No vision support — uses text description of screen only",
    },
}


# ---------------------------------------------------------------------------
# Individual provider call implementations
# ---------------------------------------------------------------------------

def _call_anthropic(model: str, system: str, prompt: str, image_b64: str | None) -> str:
    import anthropic
    client = anthropic.Anthropic()
    content = []
    if image_b64:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": image_b64},
        })
    content.append({"type": "text", "text": prompt})
    resp = client.messages.create(
        model=model, max_tokens=512, system=system,
        messages=[{"role": "user", "content": content}],
    )
    return resp.content[0].text.strip()


def _call_openai_compat(
    model: str, system: str, prompt: str, image_b64: str | None,
    api_key: str, base_url: str | None = None
) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    content = []
    if image_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_b64}", "detail": "high"},
        })
    content.append({"type": "text", "text": prompt})
    resp = client.chat.completions.create(
        model=model, max_tokens=512,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
    )
    return resp.choices[0].message.content.strip()


def _call_gemini(model: str, system: str, prompt: str, image_b64: str | None) -> str:
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    m = genai.GenerativeModel(model, system_instruction=system)
    parts = []
    if image_b64:
        import PIL.Image, io
        img = PIL.Image.open(io.BytesIO(base64.b64decode(image_b64)))
        parts.append(img)
    parts.append(prompt)
    resp = m.generate_content(parts, generation_config={"max_output_tokens": 512})
    return resp.text.strip()


def _call_groq(model: str, system: str, prompt: str, image_b64: str | None) -> str:
    from groq import Groq
    client = Groq()
    content = []
    if image_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_b64}"},
        })
    content.append({"type": "text", "text": prompt})
    resp = client.chat.completions.create(
        model=model, max_tokens=512,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
    )
    return resp.choices[0].message.content.strip()


def _call_mistral(model: str, system: str, prompt: str, image_b64: str | None) -> str:
    from mistralai import Mistral
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    content = []
    if image_b64:
        content.append({
            "type": "image_url",
            "image_url": f"data:image/png;base64,{image_b64}",
        })
    content.append({"type": "text", "text": prompt})
    resp = client.chat.complete(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
    )
    return resp.choices[0].message.content.strip()


def _call_together(model: str, system: str, prompt: str, image_b64: str | None) -> str:
    from together import Together
    client = Together()
    content = []
    if image_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_b64}"},
        })
    content.append({"type": "text", "text": prompt})
    resp = client.chat.completions.create(
        model=model, max_tokens=512,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
    )
    return resp.choices[0].message.content.strip()


def _call_azure(model: str, system: str, prompt: str, image_b64: str | None) -> str:
    from openai import AzureOpenAI
    client = AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    )
    content = []
    if image_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_b64}", "detail": "high"},
        })
    content.append({"type": "text", "text": prompt})
    resp = client.chat.completions.create(
        model=model, max_tokens=512,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
    )
    return resp.choices[0].message.content.strip()


def _call_cohere(model: str, system: str, prompt: str, image_b64: str | None) -> str:
    import cohere
    full_prompt = f"{system}\n\n{prompt}"
    if image_b64:
        full_prompt += "\n\n[Note: Vision not available. Describe your best guess based on context.]"
    try:
        # cohere v5+ (ClientV2)
        client = cohere.ClientV2(os.environ["COHERE_API_KEY"])
        resp = client.chat(
            model=model,
            messages=[{"role": "user", "content": full_prompt}],
        )
        return resp.message.content[0].text.strip()
    except AttributeError:
        # cohere v4 fallback
        client = cohere.Client(os.environ["COHERE_API_KEY"])
        resp = client.chat(model=model, message=full_prompt)
        return resp.text.strip()


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------

def call_provider(
    provider: str,
    system: str,
    prompt: str,
    image_b64: str | None,
    model: str | None = None,
) -> str:
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider '{provider}'. Choose from: {list(PROVIDERS)}")

    info = PROVIDERS[provider]
    model = model or info["default_model"]

    if provider == "anthropic":
        return _call_anthropic(model, system, prompt, image_b64)

    elif provider == "openai":
        return _call_openai_compat(
            model, system, prompt, image_b64,
            api_key=os.environ["OPENAI_API_KEY"],
        )

    elif provider == "gemini":
        return _call_gemini(model, system, prompt, image_b64)

    elif provider == "groq":
        return _call_groq(model, system, prompt, image_b64)

    elif provider == "mistral":
        return _call_mistral(model, system, prompt, image_b64)

    elif provider == "together":
        return _call_together(model, system, prompt, image_b64)

    elif provider in ("ollama", "lmstudio", "llamacpp"):
        return _call_openai_compat(
            model, system, prompt, image_b64,
            api_key="local",
            base_url=info["base_url"],
        )

    elif provider == "azure":
        return _call_azure(model, system, prompt, image_b64)

    elif provider == "deepseek":
        return _call_openai_compat(
            model, system, prompt, None,  # no vision
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url=info["base_url"],
        )

    elif provider == "cohere":
        return _call_cohere(model, system, prompt, image_b64)

    raise ValueError(f"Provider '{provider}' not implemented")


def list_providers() -> None:
    print("\nSupported providers:")
    print(f"  {'Provider':<12} {'Default Model':<42} {'Vision':<8} Env Key")
    print("  " + "-" * 85)
    for key, info in PROVIDERS.items():
        vision = "[vision]" if info["vision"] else "[text] "
        env = info["env_key"] or "none (local)"
        print(f"  {key:<12} {info['default_model']:<42} {vision:<8} {env}")
    print()
