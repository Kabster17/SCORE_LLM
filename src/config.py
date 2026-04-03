"""Central configuration helpers for the SCORE repository."""

from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class GenerationConfig:
    """Configuration for repeated response generation."""

    temperature: float = 0.3
    top_p: float = 0.6
    max_tokens: int = 512
    num_attempts: int = 3
    max_questions: int = 20



def get_api_key(provider: str) -> str:
    """Return the API key for the requested provider."""
    provider = provider.lower()
    mapping = {
        "openai": os.getenv("OPENAI_API_KEY", ""),
        "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
        "deepseek": os.getenv("DEEPSEEK_API_KEY", ""),
    }
    if provider not in mapping:
        raise ValueError(f"Unsupported provider: {provider}")
    return mapping[provider]
