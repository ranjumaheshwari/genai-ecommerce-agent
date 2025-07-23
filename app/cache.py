"""
Simple in-memory caching system for LLM responses
"""
import hashlib
import json
import time
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from threading import Lock

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with data and metadata"""
    data: Any
    timestamp: float
    access_count: int = 0
    last_accessed: float = None

class SimpleCache:
    """
    Simple in-memory cache with TTL and LRU eviction
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize cache
        
        Args:
            max_size: Maximum number of entries to store
            default_ttl: Default time-to-live in seconds (1 hour)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        
        logger.info(f"Cache initialized with max_size={max_size}, ttl={default_ttl}s")
    
    def _generate_key(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        Generate a cache key from query and context
        
        Args:
            query: The user query
            context: Additional context (e.g., database schema hash)
            
        Returns:
            str: Cache key
        """
        # Normalize query (lowercase, strip whitespace)
        normalized_query = query.lower().strip()
        
        # Create cache key from query and context
        cache_data = {
            "query": normalized_query,
            "context": context or {}
        }
        
        # Generate hash
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def get(self, query: str, context: Dict[str, Any] = None) -> Optional[Any]:
        """
        Get cached response for a query
        
        Args:
            query: The user query
            context: Additional context
            
        Returns:
            Cached data or None if not found/expired
        """
        key = self._generate_key(query, context)
        
        with self._lock:
            if key not in self._cache:
                logger.debug(f"Cache miss for key: {key[:8]}...")
                return None
            
            entry = self._cache[key]
            current_time = time.time()
            
            # Check if expired
            if current_time - entry.timestamp > self.default_ttl:
                logger.debug(f"Cache expired for key: {key[:8]}...")
                del self._cache[key]
                return None
            
            # Update access statistics
            entry.access_count += 1
            entry.last_accessed = current_time
            
            logger.debug(f"Cache hit for key: {key[:8]}... (accessed {entry.access_count} times)")
            return entry.data
    
    def set(self, query: str, data: Any, context: Dict[str, Any] = None, ttl: int = None) -> None:
        """
        Store data in cache
        
        Args:
            query: The user query
            data: Data to cache
            context: Additional context
            ttl: Time-to-live override
        """
        key = self._generate_key(query, context)
        current_time = time.time()
        
        with self._lock:
            # Check if we need to evict entries
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            # Store new entry
            self._cache[key] = CacheEntry(
                data=data,
                timestamp=current_time,
                last_accessed=current_time
            )
            
            logger.debug(f"Cached data for key: {key[:8]}... (cache size: {len(self._cache)})")
    
    def _evict_lru(self) -> None:
        """Evict least recently used entries"""
        if not self._cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed or self._cache[k].timestamp
        )
        
        del self._cache[lru_key]
        logger.debug(f"Evicted LRU entry: {lru_key[:8]}...")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_accesses = sum(entry.access_count for entry in self._cache.values())
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "total_accesses": total_accesses,
                "hit_rate": 0.0 if total_accesses == 0 else total_accesses / len(self._cache),
                "oldest_entry": min(
                    (entry.timestamp for entry in self._cache.values()),
                    default=None
                ),
                "newest_entry": max(
                    (entry.timestamp for entry in self._cache.values()),
                    default=None
                )
            }
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed entries"""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, entry in self._cache.items():
                if current_time - entry.timestamp > self.default_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)

# Global cache instance
query_cache = SimpleCache(max_size=500, default_ttl=1800)  # 30 minutes TTL
