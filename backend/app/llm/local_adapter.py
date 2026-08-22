import asyncio
import hashlib
import math
import re
from typing import AsyncGenerator, Dict, List
from backend.app.llm.base import BaseEmbeddingAdapter, BaseLLMAdapter
from backend.app.core.logging import logger

class LocalEmbeddingAdapter(BaseEmbeddingAdapter):
    """
    High-performance, zero-dependency local embedding engine.
    Uses n-gram character/word hash projection with sub-word frequency
    weighting and L2 normalization to produce 384-dimensional dense vectors.
    """

    def __init__(self, dimension: int = 384):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def provider_name(self) -> str:
        return "local-ngram-projector"

    def _embed_single(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self._dim

        vector = [0.0] * self._dim
        clean_text = text.lower().strip()
        tokens = re.findall(r"\b\w+\b", clean_text)
        
        # Word tokens
        for i, token in enumerate(tokens):
            # Compute multiple hash projections
            h1 = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self._dim
            h2 = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16) % self._dim
            weight = 1.0 / math.sqrt(len(token) + 1)
            vector[h1] += weight
            vector[h2] += (weight * 0.5)

            # Bi-grams
            if i < len(tokens) - 1:
                bigram = f"{token}_{tokens[i+1]}"
                h_bi = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16) % self._dim
                vector[h_bi] += 1.5

        # Character tri-grams for fuzzy matching
        for j in range(len(clean_text) - 2):
            trigram = clean_text[j:j+3]
            h_tri = int(hashlib.md5(trigram.encode("utf-8")).hexdigest(), 16) % self._dim
            vector[h_tri] += 0.3

        # L2 Normalization
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [round(x / norm, 6) for x in vector]
        return vector

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_single(t) for t in texts]

    async def embed_query(self, query: str) -> List[float]:
        return self._embed_single(query)

class LocalLLMAdapter(BaseLLMAdapter):
    """
    Zero-config local synthesis engine for offline/keyless demonstration.
    Synthesizes facts from retrieved context chunks and streams structured answers.
    """

    def __init__(self, model_name: str = "local-heuristic-synthesizer"):
        self._model_name = model_name

    @property
    def provider_name(self) -> str:
        return "local"

    @property
    def model_name(self) -> str:
        return self._model_name

    def _extract_and_synthesize(self, prompt: str) -> str:
        # Prompt contains the context blocks: "--- Source [1] ... ---"
        # and the user question at the end: "Question: ..."
        question_match = re.search(r"Question:\s*(.+)", prompt, re.DOTALL | re.IGNORECASE)
        question = question_match.group(1).strip() if question_match else "your query"

        # Extract context chunks
        context_blocks = re.findall(
            r"--- Source \[\d+\]\s*\(([^)]+)\)\s*---\n(.*?)(?=\n--- Source|\n\nBased on|$)",
            prompt,
            re.DOTALL
        )

        if not context_blocks:
            # Fallback if format is different
            context_blocks = [("Saved Notes", prompt)]

        synthesized_points = []
        q_words = set(re.findall(r"\b\w{3,}\b", question.lower()))

        for src_title, src_text in context_blocks:
            lines = [l.strip() for l in src_text.split("\n") if len(l.strip()) > 15]
            scored_lines = []
            for line in lines:
                l_words = set(re.findall(r"\b\w{3,}\b", line.lower()))
                common = q_words.intersection(l_words)
                score = len(common) * 2 + (len(line) / 200.0)
                scored_lines.append((score, line))
            
            scored_lines.sort(key=lambda x: x[0], reverse=True)
            top_lines = [l for _, l in scored_lines[:2]]
            if top_lines:
                synthesized_points.append(f"**From {src_title.strip()}:**\n" + "\n".join(f"- {l}" for l in top_lines))

        if not synthesized_points:
            answer = (
                f"Based on your saved knowledge items, here is the relevant context regarding **{question}**:\n\n"
                f"The retrieved records contain information matching your search. Review the cited sources below for the full snippets."
            )
        else:
            joined_points = "\n\n".join(synthesized_points)
            answer = (
                f"### Answer Summary\n\n"
                f"Based on your saved notes and ingested URLs, here is the synthesized answer regarding **{question}**:\n\n"
                f"{joined_points}\n\n"
                f"*Note: Running with local offline synthesizer. Configure an `OPENAI_API_KEY`, `GEMINI_API_KEY`, or `GROQ_API_KEY` in `.env` for generative neural answers.*"
            )

        return answer

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        await asyncio.sleep(0.05)
        return self._extract_and_synthesize(prompt)

    async def generate_stream(self, prompt: str, system_prompt: str = "") -> AsyncGenerator[str, None]:
        full_text = self._extract_and_synthesize(prompt)
        words = full_text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield chunk
            await asyncio.sleep(0.015)
