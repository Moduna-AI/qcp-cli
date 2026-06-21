"""LangChain model construction and Gemini credential validation."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from qcp import config as cfg
from qcp.errors import NoApiKeyConfiguredError

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def get_model() -> str:
    """Resolve the Gemini model from environment, config, or default."""
    return str(os.environ.get("GEMINI_MODEL") or cfg.get("gemini_model") or DEFAULT_GEMINI_MODEL)


def require_api_key() -> str:
    """Return the configured Gemini key or raise an actionable error."""
    api_key = cfg.get_gemini_api_key()
    if not api_key:
        raise NoApiKeyConfiguredError("gemini")
    return api_key


class ChatModelFactory(ABC):
    """Contract for constructing the chat model used by QCP agents."""

    @abstractmethod
    def create(self) -> BaseChatModel:
        """Create a configured LangChain chat model."""


class GeminiChatModelFactory(ChatModelFactory):
    """Create Gemini 2.5 Flash models through LangChain."""

    def __init__(self, api_key: str, model: str | None = None) -> None:
        """Initialize explicit credentials and model selection."""
        self._api_key = api_key
        self._model = model or get_model()

    def create(self) -> ChatGoogleGenerativeAI:
        """Create a deterministic Gemini chat model with tool support."""
        return ChatGoogleGenerativeAI(
            model=self._model,
            google_api_key=self._api_key,
            temperature=0.1,
        )


def validate_api_key(api_key: str) -> tuple[bool, str]:
    """Validate a Gemini key through the same LangChain integration QCP uses."""
    try:
        GeminiChatModelFactory(api_key).create().invoke("Reply with the single word pong.")
    except Exception as error:
        return False, str(error)[:300]
    return True, ""
