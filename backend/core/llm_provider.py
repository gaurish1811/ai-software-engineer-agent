import os
import httpx
from typing import Dict, Any, Optional
from backend.config import settings

class LLMProvider:
    """Unified interface to call OpenAI, Anthropic Claude, Google Gemini, or Ollama."""

    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        self.provider = (provider or settings.DEFAULT_PROVIDER).lower()
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, system_prompt: str = "You are an expert AI Software Engineer.") -> str:
        """Executes LLM request using selected provider or fallback."""
        
        if self.provider == "openai":
            return self._call_openai(prompt, system_prompt)
        elif self.provider == "anthropic":
            return self._call_anthropic(prompt, system_prompt)
        elif self.provider == "gemini":
            return self._call_gemini(prompt, system_prompt)
        elif self.provider == "ollama":
            return self._call_ollama(prompt, system_prompt)
        else:
            # Fallback to OpenAI -> Gemini -> Ollama fallback
            return self._fallback_chain(prompt, system_prompt)

    def _call_openai(self, prompt: str, system_prompt: str) -> str:
        key = self.api_key or settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
        if not key:
            # Try Gemini fallback if OpenAI key missing
            if settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY"):
                return self._call_gemini(prompt, system_prompt)
            raise ValueError("OpenAI API key missing. Please configure OPENAI_API_KEY in settings or environment.")

        from openai import OpenAI
        client = OpenAI(api_key=key)
        model_name = self.model or settings.OPENAI_MODEL
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content or ""

    def _call_anthropic(self, prompt: str, system_prompt: str) -> str:
        key = self.api_key or settings.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("Anthropic API key missing. Please configure ANTHROPIC_API_KEY in settings or environment.")

        from anthropic import Anthropic
        client = Anthropic(api_key=key)
        model_name = self.model or settings.ANTHROPIC_MODEL

        response = client.messages.create(
            model=model_name,
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def _call_gemini(self, prompt: str, system_prompt: str) -> str:
        key = self.api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ValueError("Gemini API key missing. Please configure GEMINI_API_KEY in settings or environment.")

        from google import genai
        client = genai.Client(api_key=key)
        model_name = self.model or settings.GEMINI_MODEL

        full_prompt = f"{system_prompt}\n\nTask:\n{prompt}"
        response = client.models.generate_content(
            model=model_name,
            contents=full_prompt
        )
        return response.text or ""

    def _call_ollama(self, prompt: str, system_prompt: str) -> str:
        model_name = self.model or settings.OLLAMA_MODEL
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        
        payload = {
            "model": model_name,
            "prompt": f"{system_prompt}\n\n{prompt}",
            "stream": False
        }
        
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                return resp.json().get("response", "")
            else:
                raise ValueError(f"Ollama server error ({resp.status_code}): {resp.text}")

    def _fallback_chain(self, prompt: str, system_prompt: str) -> str:
        providers = [
            ("openai", settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")),
            ("anthropic", settings.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY")),
            ("gemini", settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY"))
        ]
        
        for prov, key in providers:
            if key:
                self.provider = prov
                return self.generate(prompt, system_prompt)

        # Try local Ollama as final attempt
        try:
            return self._call_ollama(prompt, system_prompt)
        except Exception:
            raise ValueError("No active API keys found for OpenAI, Anthropic, or Gemini, and local Ollama is not running. Please provide an API key in Settings.")
