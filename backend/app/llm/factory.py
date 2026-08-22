from typing import Tuple
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.llm.base import BaseEmbeddingAdapter, BaseLLMAdapter
from backend.app.llm.local_adapter import LocalEmbeddingAdapter, LocalLLMAdapter
from backend.app.llm.openai_adapter import OpenAIEmbeddingAdapter, OpenAILLMAdapter
from backend.app.llm.gemini_adapter import GeminiEmbeddingAdapter, GeminiLLMAdapter

class AIProviderFactory:
    """Factory to resolve LLM and Embedding adapters based on config & available API keys."""

    @staticmethod
    def get_embedding_adapter() -> BaseEmbeddingAdapter:
        requested = settings.EMBEDDING_PROVIDER.lower().strip()

        if (requested in ("auto", "openai")) and settings.OPENAI_API_KEY:
            logger.info("Initializing OpenAI Embedding Adapter.")
            return OpenAIEmbeddingAdapter()

        if (requested in ("auto", "gemini")) and settings.GEMINI_API_KEY:
            logger.info("Initializing Gemini Embedding Adapter.")
            return GeminiEmbeddingAdapter()

        logger.info("Initializing Zero-Config Local Embedding Adapter.")
        return LocalEmbeddingAdapter()

    @staticmethod
    def get_llm_adapter() -> BaseLLMAdapter:
        requested = settings.LLM_PROVIDER.lower().strip()

        if (requested in ("auto", "openai")) and settings.OPENAI_API_KEY:
            logger.info("Initializing OpenAI LLM Adapter.")
            return OpenAILLMAdapter()

        if (requested in ("auto", "groq")) and settings.GROQ_API_KEY:
            logger.info("Initializing Groq LLM Adapter.")
            return OpenAILLMAdapter(
                api_key=settings.GROQ_API_KEY,
                model=settings.GROQ_MODEL,
                base_url="https://api.groq.com/openai/v1",
                provider_name="groq"
            )

        if (requested in ("auto", "gemini")) and settings.GEMINI_API_KEY:
            logger.info("Initializing Gemini LLM Adapter.")
            return GeminiLLMAdapter()

        logger.info("Initializing Zero-Config Local Heuristic Synthesizer LLM Adapter.")
        return LocalLLMAdapter()

    @classmethod
    def get_adapters(cls) -> Tuple[BaseEmbeddingAdapter, BaseLLMAdapter]:
        return cls.get_embedding_adapter(), cls.get_llm_adapter()

ai_factory = AIProviderFactory()
