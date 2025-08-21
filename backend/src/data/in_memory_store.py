import time
from threading import Lock
from typing import Dict, Any, Tuple

class TokenBucket:
    """A token bucket implementation for rate limiting."""
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.monotonic()

    def consume(self) -> bool:
        self._refill()
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        if new_tokens > 0:
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now

class InMemoryStore:
    """
    Singleton class for an in-memory database with concurrency-safe balance updates.
    """
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(InMemoryStore, cls).__new__(cls)
                cls._instance.customer_balances = {"c_123": 300.00, "c_456": 2000.00}
                cls._instance.idempotency_requests: Dict[str, Tuple[int, Any]] = {}
                cls._instance.rate_limit_buckets: Dict[str, TokenBucket] = {}
                cls._instance.balance_locks: Dict[str, Lock] = {
                    "c_123": Lock(), "c_456": Lock()
                }
        return cls._instance

    def get_balance_lock(self, customer_id: str) -> Lock:
        with self._lock:
            if customer_id not in self.balance_locks:
                self.balance_locks[customer_id] = Lock()
            return self.balance_locks[customer_id]

db = InMemoryStore()