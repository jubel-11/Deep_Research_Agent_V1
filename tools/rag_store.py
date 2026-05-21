"""
RAG Store
Embeds research findings into ChromaDB for semantic retrieval.
When the agent reads multiple pages, findings are stored here
so relevant content can be retrieved during report writing.
"""

import os
import time
import chromadb
import google.generativeai as genai
from chromadb.utils.embedding_functions import EmbeddingFunction
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class GeminiEmbeddingFunction(EmbeddingFunction):
    """Gemini embedding function for ChromaDB."""
    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = []
        for text in input:
            try:
                result = genai.embed_content(
                    model="models/gemini-embedding-001",
                    content=text[:2000],  # truncate for embedding
                )
                embeddings.append(result["embedding"])
                time.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️  Embedding error: {e}")
                embeddings.append([0.0] * 768)
        return embeddings


class ResearchRAGStore:
    """
    In-memory + ChromaDB store for research findings.
    Stores page content as chunks for semantic retrieval
    during report generation.
    """

    def __init__(self, session_id: str = "research_session"):
        self.session_id   = session_id
        self.embedding_fn = GeminiEmbeddingFunction()

        # Use in-memory ChromaDB (no disk needed for one session)
        self.client     = chromadb.Client()
        self.collection = self.client.get_or_create_collection(
            name=f"research_{session_id[:20]}",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        self._chunk_counter = 0

    def add_page(self, url: str, title: str, content: str):
        """
        Add a researched page to the RAG store.
        Splits content into chunks and embeds each one.
        """
        if not content or len(content) < 50:
            return

        # Simple chunking: split on double newlines, max 500 chars
        chunks = []
        paragraphs = content.split("\n\n")
        current    = ""

        for para in paragraphs:
            if len(current) + len(para) < 500:
                current += para + "\n\n"
            else:
                if current.strip():
                    chunks.append(current.strip())
                current = para + "\n\n"
        if current.strip():
            chunks.append(current.strip())

        # Filter very short chunks
        chunks = [c for c in chunks if len(c) > 50]

        if not chunks:
            return

        ids       = [f"chunk_{self._chunk_counter + i}" for i in range(len(chunks))]
        metadatas = [{"url": url, "title": title, "chunk": i} for i in range(len(chunks))]

        try:
            self.collection.upsert(
                ids=ids,
                documents=chunks,
                metadatas=metadatas,
            )
            self._chunk_counter += len(chunks)
        except Exception as e:
            print(f"  ⚠️  RAG store error: {e}")

    def retrieve(self, query: str, top_k: int = 4) -> List[dict]:
        """
        Retrieve most relevant chunks for a query.

        Returns list of dicts with content, url, title, similarity.
        """
        if self.collection.count() == 0:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, self.collection.count()),
                include=["documents", "metadatas", "distances"],
            )

            output = []
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                output.append({
                    "content":    doc,
                    "url":        meta.get("url", ""),
                    "title":      meta.get("title", ""),
                    "similarity": round(1 - dist, 3),
                })
            return output

        except Exception as e:
            print(f"  ⚠️  Retrieval error: {e}")
            return []

    def count(self) -> int:
        return self.collection.count()
