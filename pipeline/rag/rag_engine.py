#!/usr/bin/env python3
"""Marin Pipeline — RAG Engine for Character-Specific Knowledge

Each niche has its own RAG directory with books, stories, transcripts.
FAISS + HuggingFace embeddings for retrieval.
"""

import hashlib
import json
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    DirectoryLoader,
)
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""],
)


class NicheRAG:
    """Per-niche FAISS index with metadata."""

    def __init__(self, niche_id: str, rag_dir: Path):
        self.niche_id = niche_id
        self.rag_dir = rag_dir
        self.index_dir = rag_dir.parent / "faiss_index"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_dir / "index.faiss"
        self.meta_path = self.index_dir / "metadata.json"
        self.index: Optional[faiss.IndexFlatL2] = None
        self.documents: list[dict] = []

    def load_and_index(self) -> int:
        """Load docs from rag_dir, embed, index. Returns chunk count."""
        if not self.rag_dir.exists():
            self.rag_dir.mkdir(parents=True, exist_ok=True)
            return 0

        loaders = []
        for pattern, cls in [("**/*.pdf", PyPDFLoader), ("**/*.txt", TextLoader), ("**/*.md", TextLoader)]:
            loaders.append(DirectoryLoader(str(self.rag_dir), glob=pattern, loader_cls=cls))

        all_docs = []
        for loader in loaders:
            try:
                all_docs.extend(loader.load())
            except Exception:
                pass

        if not all_docs:
            return 0

        chunks = text_splitter.split_documents(all_docs)
        if not chunks:
            return 0

        texts = [c.page_content for c in chunks]
        metadatas = [
            {**(c.metadata if hasattr(c, "metadata") else {}), "niche": self.niche_id}
            for c in chunks
        ]

        embeddings_list = embeddings.embed_documents(texts)
        dim = len(embeddings_list[0])
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(np.array(embeddings_list, dtype=np.float32))
        self.documents = [{"text": t, "metadata": m} for t, m in zip(texts, metadatas)]

        faiss.write_index(self.index, str(self.index_path))
        with open(self.meta_path, "w") as f:
            json.dump(self.documents, f)

        print(f"[RAG:{self.niche_id}] Indexed {len(texts)} chunks")
        return len(texts)

    def load_existing(self) -> bool:
        if not self.index_path.exists() or not self.meta_path.exists():
            return False
        try:
            self.index = faiss.read_index(str(self.index_path))
            with open(self.meta_path) as f:
                self.documents = json.load(f)
            return True
        except Exception:
            return False

    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        if self.index is None or self.index.ntotal == 0:
            if not self.load_existing():
                return []

        query_emb = embeddings.embed_query(query)
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(np.array([query_emb], dtype=np.float32), k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc["score"] = float(1 / (1 + dist))
                results.append(doc)
        return results

    def add_documents(self, file_paths: list[Path]) -> int:
        new_docs = []
        for fp in file_paths:
            if not fp.exists():
                continue
            loader = PyPDFLoader(str(fp)) if fp.suffix.lower() == ".pdf" else TextLoader(str(fp))
            try:
                new_docs.extend(loader.load())
            except Exception:
                pass

        if not new_docs:
            return 0

        chunks = text_splitter.split_documents(new_docs)
        texts = [c.page_content for c in chunks]
        metadatas = [
            {**(c.metadata if hasattr(c, "metadata") else {}), "niche": self.niche_id}
            for c in chunks
        ]

        embeddings_list = embeddings.embed_documents(texts)
        vecs = np.array(embeddings_list, dtype=np.float32)

        if self.index is None:
            self.index = faiss.IndexFlatL2(len(embeddings_list[0]))

        self.index.add(vecs)
        self.documents.extend([{"text": t, "metadata": m} for t, m in zip(texts, metadatas)])

        faiss.write_index(self.index, str(self.index_path))
        with open(self.meta_path, "w") as f:
            json.dump(self.documents, f)
        return len(texts)


class RAGManager:
    """Manages all niche RAG engines."""

    def __init__(self, niches_config: dict):
        self.engines = {
            nid: NicheRAG(nid, Path(cfg["rag_dir"]))
            for nid, cfg in niches_config.items()
        }

    def index_all(self) -> dict[str, int]:
        return {nid: engine.load_and_index() for nid, engine in self.engines.items()}

    def retrieve(self, niche_id: str, query: str, k: int = 5) -> list[dict]:
        if niche_id not in self.engines:
            return []
        return self.engines[niche_id].retrieve(query, k)

    def add_to_niche(self, niche_id: str, file_paths: list[Path]) -> int:
        if niche_id not in self.engines:
            return 0
        return self.engines[niche_id].add_documents(file_paths)
