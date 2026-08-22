import asyncio
from typing import AsyncGenerator, List, Optional
import google.generativeai as genai
from backend.app.llm.base import BaseEmbeddingAdapter, BaseLLMAdapter
from backend.app.llm.local_adapter import LocalEmbeddingAdapter
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import LLMProviderError

class GeminiEmbeddingAdapter(BaseEmbeddingAdapter):
    """Google Gemini Embedding adapter with local fallback support."""

    def __init__(self, api_key: Optional[str] = None, model: str = "models/gemini-embedding-001"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self._dim = 3072
        self._local_fallback = LocalEmbeddingAdapter()

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _sync_embed(self, text: str) -> List[float]:
        models_to_try = [self.model, "models/gemini-embedding-001", "models/gemini-embedding-2", "models/embedding-001"]
        for m in models_to_try:
            try:
                res = genai.embed_content(
                    model=m,
                    content=text,
                    task_type="retrieval_document"
                )
                if "embedding" in res:
                    self._dim = len(res["embedding"])
                    return res["embedding"]
            except Exception:
                continue
        # Fallback to local deterministic embedding if API quota / model unavailable
        logger.warning("Gemini embedding endpoint unavailable, using local high-speed projector.")
        return self._local_fallback._embed_single(text)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: [self._sync_embed(t) for t in texts])

    async def embed_query(self, query: str) -> List[float]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._sync_embed(query))

class GeminiLLMAdapter(BaseLLMAdapter):
    """Google Gemini LLM adapter supporting Gemini 3.6/3.7 flash and streaming."""

    def __init__(self, api_key: Optional[str] = None, model: str = "models/gemini-3.6-flash"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.client = self._init_client()

    def _init_client(self):
        models_to_try = [self.model, "models/gemini-3.6-flash", "models/gemini-3.7-flash", "models/gemini-flash-latest", "gemini-1.5-flash"]
        for m in models_to_try:
            try:
                return genai.GenerativeModel(m)
            except Exception:
                continue
        return genai.GenerativeModel("models/gemini-3.6-flash")

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self.model

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        try:
            loop = asyncio.get_event_loop()
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = await loop.run_in_executor(None, lambda: self.client.generate_content(full_prompt))
            return response.text or ""
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise LLMProviderError("gemini", str(e))

    async def generate_stream(self, prompt: str, system_prompt: str = "") -> AsyncGenerator[str, None]:
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response_stream = self.client.generate_content(full_prompt, stream=True)
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
                    await asyncio.sleep(0.01)
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            raise LLMProviderError("gemini", str(e))
