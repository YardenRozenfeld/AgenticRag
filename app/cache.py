import logging
import uuid

import numpy as np
import redis
from langchain_openai import OpenAIEmbeddings

from app.config import get_settings

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.95
CACHE_TTL = 60 * 60 * 24 * 7  # 7 days


class SemanticCache:
    def __init__(self):
        settings = get_settings()
        self._client = redis.from_url(settings.redis_url, decode_responses=False)
        self._embeddings = OpenAIEmbeddings()

    def _embed(self, text: str) -> np.ndarray:
        vec = self._embeddings.embed_query(text)
        return np.array(vec, dtype=np.float32)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        dot = np.dot(a, b)
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        if norm == 0:
            return 0.0
        return float(dot / norm)

    def lookup(self, question: str) -> str | None:
        query_vec = self._embed(question)
        best_score = 0.0
        best_response = None

        cursor = 0
        while True:
            cursor, keys = self._client.scan(cursor, match="cache:*", count=100)
            for key in keys:
                data = self._client.hgetall(key)
                if not data:
                    continue
                stored_vec = np.frombuffer(data[b"embedding"], dtype=np.float32)
                score = self._cosine_similarity(query_vec, stored_vec)
                if score > best_score:
                    best_score = score
                    best_response = data[b"response"].decode("utf-8")
            if cursor == 0:
                break

        if best_score >= SIMILARITY_THRESHOLD:
            logger.info("Cache hit (similarity=%.4f)", best_score)
            return best_response
        return None

    def store(self, question: str, response: str) -> None:
        vec = self._embed(question)
        key = f"cache:{uuid.uuid4()}"
        self._client.hset(
            key,
            mapping={
                "question": question.encode("utf-8"),
                "embedding": vec.tobytes(),
                "response": response.encode("utf-8"),
            },
        )
        self._client.expire(key, CACHE_TTL)


_cache_instance: SemanticCache | None = None


def get_semantic_cache() -> SemanticCache | None:
    global _cache_instance
    settings = get_settings()
    if not settings.redis_url:
        return None
    if _cache_instance is None:
        try:
            _cache_instance = SemanticCache()
            _cache_instance._client.ping()
        except Exception:
            logger.warning("Redis unavailable, semantic cache disabled")
            _cache_instance = None
    return _cache_instance
