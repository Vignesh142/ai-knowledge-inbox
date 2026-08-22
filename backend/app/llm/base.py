from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Tuple

class BaseEmbeddingAdapter(ABC):
    """Abstract interface for generating vector embeddings."""

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a list of text strings."""
        pass

    @abstractmethod
    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding vector for a single search query."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding dimension size."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier."""
        pass

class BaseLLMAdapter(ABC):
    """Abstract interface for LLM synthesis and streaming."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a complete text answer from prompt context."""
        pass

    @abstractmethod
    async def generate_stream(self, prompt: str, system_prompt: str = "") -> AsyncGenerator[str, None]:
        """Generate text answer token by token in an async stream."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model name."""
        pass
