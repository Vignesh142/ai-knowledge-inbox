import json
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.domain import SourceCitation
from backend.app.models.schemas import QueryRequest, QueryResponse, SourceCitationSchema
from backend.app.vector_store.base import BaseVectorStore
from backend.app.vector_store.chroma_store import ChromaVectorStore
from backend.app.llm.base import BaseEmbeddingAdapter, BaseLLMAdapter
from backend.app.llm.factory import ai_factory

SYSTEM_RAG_PROMPT = """You are an intelligent AI Knowledge Assistant.
Your task is to answer the user's question accurately and concisely based ONLY on the provided context sources from their saved notes and bookmarked URLs.

Guidelines:
1. Ground your answer in the provided context sources.
2. If the context does not contain enough information to fully answer the question, clearly acknowledge what is known from the notes and state what is missing.
3. Reference sources naturally or use markdown brackets like [Source 1], [Source 2] where appropriate.
4. Format your answer with clean Markdown, bullet points, and headings for maximum readability.
"""

class RAGService:
    """Orchestrates Semantic Vector Search and LLM Question-Answering pipeline."""

    def __init__(
        self,
        vector_store: Optional[BaseVectorStore] = None,
        embedding_adapter: Optional[BaseEmbeddingAdapter] = None,
        llm_adapter: Optional[BaseLLMAdapter] = None,
    ):
        self.vector_store = vector_store or ChromaVectorStore()
        self.embedding_adapter = embedding_adapter or ai_factory.get_embedding_adapter()
        self.llm_adapter = llm_adapter or ai_factory.get_llm_adapter()

    async def retrieve_context(
        self,
        question: str,
        top_k: int = settings.TOP_K_RETRIEVAL,
        item_type_filter: Optional[str] = None,
    ) -> List[SourceCitation]:
        logger.info(f"Retrieving top {top_k} vector matches for question: '{question}'")
        # 1. Embed query
        query_embedding = await self.embedding_adapter.embed_query(question)

        # 2. Build filters
        filters = {}
        if item_type_filter:
            filters["type"] = item_type_filter

        # 3. Query Vector Store
        matches = await self.vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters if filters else None,
        )

        citations: List[SourceCitation] = []
        for chunk_id, doc_text, meta, score in matches:
            # Only include if above minimal similarity threshold or fallback if list is empty
            if score >= settings.SIMILARITY_THRESHOLD or not citations:
                citations.append(
                    SourceCitation(
                        chunk_id=chunk_id,
                        item_id=meta.get("item_id", ""),
                        item_title=meta.get("title", "Untitled Document"),
                        item_type=meta.get("type", "note"),
                        url=meta.get("url") if meta.get("url") else None,
                        snippet=doc_text.strip(),
                        similarity_score=round(score, 4),
                        chunk_index=int(meta.get("chunk_index", 0)),
                    )
                )

        logger.info(f"Retrieved {len(citations)} relevant citations (top score: {citations[0].similarity_score if citations else 0.0}).")
        return citations

    def _build_prompt(self, question: str, citations: List[SourceCitation]) -> str:
        if not citations:
            return f"No relevant saved items found in knowledge inbox.\n\nQuestion: {question}"

        context_blocks = []
        for idx, cit in enumerate(citations, 1):
            src_type = f"URL: {cit.url}" if cit.url else "Personal Note"
            block = (
                f"--- Source [{idx}] ({cit.item_title} | {src_type} | Relevance: {int(cit.similarity_score * 100)}%) ---\n"
                f"{cit.snippet}\n"
            )
            context_blocks.append(block)

        context_str = "\n".join(context_blocks)
        prompt = (
            f"Context from Saved Knowledge Items:\n"
            f"====================================\n"
            f"{context_str}\n"
            f"====================================\n\n"
            f"User Question: {question}\n\n"
            f"Please synthesize an accurate, well-structured response based on the context above:"
        )
        return prompt

    async def answer_query(self, request: QueryRequest) -> QueryResponse:
        start_time = time.perf_counter()
        citations = await self.retrieve_context(
            question=request.question,
            top_k=request.top_k,
            item_type_filter=request.item_type_filter,
        )

        if not citations:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return QueryResponse(
                answer="I couldn't find any relevant notes or saved URLs in your knowledge inbox matching this question. Try saving relevant notes or articles first!",
                question=request.question,
                citations=[],
                retrieval_count=0,
                latency_ms=elapsed_ms,
                provider_used=self.llm_adapter.provider_name,
                model_used=self.llm_adapter.model_name,
            )

        prompt = self._build_prompt(request.question, citations)
        answer = await self.llm_adapter.generate(prompt=prompt, system_prompt=SYSTEM_RAG_PROMPT)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        schema_citations = [
            SourceCitationSchema(
                chunk_id=c.chunk_id,
                item_id=c.item_id,
                item_title=c.item_title,
                item_type=c.item_type,
                url=c.url,
                snippet=c.snippet,
                similarity_score=c.similarity_score,
                chunk_index=c.chunk_index,
            )
            for c in citations
        ]

        return QueryResponse(
            answer=answer,
            question=request.question,
            citations=schema_citations,
            retrieval_count=len(citations),
            latency_ms=elapsed_ms,
            provider_used=self.llm_adapter.provider_name,
            model_used=self.llm_adapter.model_name,
        )

    async def stream_query(self, request: QueryRequest) -> AsyncGenerator[str, None]:
        start_time = time.perf_counter()
        citations = await self.retrieve_context(
            question=request.question,
            top_k=request.top_k,
            item_type_filter=request.item_type_filter,
        )

        # Emit sources first
        sources_payload = [
            {
                "chunk_id": c.chunk_id,
                "item_id": c.item_id,
                "item_title": c.item_title,
                "item_type": c.item_type,
                "url": c.url,
                "snippet": c.snippet,
                "similarity_score": c.similarity_score,
                "chunk_index": c.chunk_index,
            }
            for c in citations
        ]

        yield f"event: sources\ndata: {json.dumps(sources_payload)}\n\n"

        if not citations:
            no_info = "I couldn't find any relevant notes or saved URLs in your knowledge inbox matching this question. Try saving notes or URLs first!"
            yield f"event: token\ndata: {json.dumps(no_info)}\n\n"
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            yield f"event: done\ndata: {json.dumps({'latency_ms': elapsed_ms, 'provider': self.llm_adapter.provider_name, 'model': self.llm_adapter.model_name})}\n\n"
            return

        prompt = self._build_prompt(request.question, citations)

        # Stream tokens
        async for token in self.llm_adapter.generate_stream(prompt=prompt, system_prompt=SYSTEM_RAG_PROMPT):
            yield f"event: token\ndata: {json.dumps(token)}\n\n"

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        done_payload = {
            "latency_ms": elapsed_ms,
            "provider": self.llm_adapter.provider_name,
            "model": self.llm_adapter.model_name,
            "citation_count": len(citations),
        }
        yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

rag_service = RAGService()
