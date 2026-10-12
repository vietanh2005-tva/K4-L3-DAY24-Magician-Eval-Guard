"""A process-wide request pacer shared by sync and async HTTP clients.

Hook it immediately before HTTP sends so SDK retries also consume a slot.
It does not reserve future slots: cancellation while waiting changes nothing.
"""

import asyncio
import threading
import time


class RequestPacer:
    def __init__(self, requests_per_minute: int = 12):
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be positive")
        # Small margin keeps even rolling 60-second windows below the limit.
        self.interval = 60.0 / requests_per_minute + 0.1
        self._next_request = 0.0
        self._lock = threading.Lock()

    def _try_acquire(self) -> float:
        with self._lock:
            now = time.monotonic()
            delay = self._next_request - now
            if delay <= 0:
                self._next_request = now + self.interval
                return 0.0
            return delay

    def wait(self, request=None):
        while True:
            delay = self._try_acquire()
            if delay <= 0:
                return
            time.sleep(delay)

    async def wait_async(self, request=None):
        while True:
            delay = self._try_acquire()
            if delay <= 0:
                return
            await asyncio.sleep(delay)


# One budget for generation, evaluation, embeddings, and retry attempts.
API_PACER = RequestPacer(requests_per_minute=12)
