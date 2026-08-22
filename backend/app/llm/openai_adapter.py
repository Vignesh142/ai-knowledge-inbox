from typing import AsyncGenerator, List, Optional
from openai import AsyncOpenAI
from backend.app.llm.base import BaseEmbeddingAdapter, BaseLLMAdapter
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import EmbeddingError, LLMProviderError

class OpenAIEmbeddingAdapter(BaseEmbeddingAdapter):
    """OpenAI embedding model adapter (e.g. text-embedding-3-small)."""

    def __init__(self, api_key: Optional[str] = None, model: str = settings.OPENAI_EMBEDDING_MODEL):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        self.client = AsyncOpenAI(api_key=self.api_key)
        self._dim = 1536

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def provider_name(self) -> str:
        return "openai"

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            # Batch embeddings in chunks of 50
            results = []
            batch_size = 50
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = await self.client.embeddings.create(
                    input=batch,
                    model=self.model
                )
                results.extend([item.embedding for item in response.data])
            return results
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise EmbeddingError(str(e))

    async def embed_query(self, query: str) -> List[float]:
        try:
            response = await self.client.embeddings.create(
                input=[query],
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI query embedding error: {e}")
            raise EmbeddingError(str(e))

class OpenAILLMAdapter(BaseLLMAdapter):
    """OpenAI / Groq LLM adapter with full streaming support."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = settings.OPENAI_MODEL,
        base_url: Optional[str] = None,
        provider_name: str = "openai"
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        self._provider_name = provider_name
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=base_url)

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model_name(self) -> str:
        return self.model

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI chat completion error: {e}")
            raise LLMProviderError(self._provider_name, str(e))

    async def generate_stream(self, prompt: str, system_prompt: str = "") -> AsyncGenerator[str, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenAI stream completion error: {e}")
            raise LLMProviderError(self._provider_name, str(e))
