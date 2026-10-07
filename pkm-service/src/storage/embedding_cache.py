"""Embedding cache — persists {content_hash → embedding_vector} to a JSON file.

Avoids redundant API calls when knowledge content is unchanged.
Cache file lives at knowledge_base/embedding_cache.json.
"""
import json
import os
import hashlib
import logging
import threading
from typing import List, Optional, Dict, Any

from core.config import settings

logger = logging.getLogger(__name__)

_CACHE_FILENAME = "embedding_cache.json"


def _content_hash(text: str) -> str:
    """SHA-256 hash of text, used as cache key."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class EmbeddingCache:
    """Thread-safe in-memory + file-backed embedding cache."""

    def __init__(self):
        self._cache_file = os.path.join(settings.knowledge_base_path, _CACHE_FILENAME)
        self._cache: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._load()

    def _load(self):
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                logger.info(f"Embedding cache loaded: {len(self._cache)} entries")
        except Exception as e:
            logger.warning(f"Failed to load embedding cache: {e}")
            self._cache = {}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self._cache_file), exist_ok=True)
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f)
        except Exception as e:
            logger.warning(f"Failed to save embedding cache: {e}")

    def get(self, text: str) -> Optional[List[float]]:
        """Return cached embedding or None."""
        key = _content_hash(text)
        with self._lock:
            result = self._cache.get(key)
            if result is not None:
                self._hits += 1
            else:
                self._misses += 1
            return result

    def set(self, text: str, embedding: List[float]) -> None:
        """Store embedding in cache."""
        key = _content_hash(text)
        with self._lock:
            self._cache[key] = embedding
        self._save()

    def stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        hit_rate = round(self._hits / total * 100, 2) if total > 0 else 0.0
        return {
            "cached_entries": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_pct": hit_rate,
        }

    def clear(self) -> None:
        with self._lock:
            self._cache = {}
        self._save()


# Singleton
embedding_cache = EmbeddingCache()
