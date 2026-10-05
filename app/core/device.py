"""Device ID pool manager."""

from __future__ import annotations

import random
import uuid
from typing import Literal

Strategy = Literal["single", "random", "pool"]


class DevicePool:
    """Manage device ID sesuai strategi.

    Attributes:
        strategy: Strategi yang dipakai.
        size: Ukuran pool kalau strategy = 'pool'.
    """

    def __init__(self, strategy: Strategy = "pool", size: int = 50) -> None:
        """Inisialisasi DevicePool.

        Args:
            strategy: 'single' | 'random' | 'pool'.
            size: Jumlah UUID dalam pool.
        """
        self.strategy: Strategy = strategy
        self.size = max(1, size)
        self._single: str = str(uuid.uuid4())
        self._pool: list[str] = [str(uuid.uuid4()) for _ in range(self.size)]
        self._idx: int = 0

    def next(self) -> str:
        """Ambil device ID berikutnya sesuai strategi.

        Returns:
            Device ID (UUID string).
        """
        if self.strategy == "single":
            return self._single
        if self.strategy == "random":
            return str(uuid.uuid4())
        device = self._pool[self._idx % len(self._pool)]
        self._idx += 1
        return device

    def random_from_pool(self) -> str:
        """Ambil UUID random dari pool.

        Returns:
            Device ID random dari pool.
        """
        return random.choice(self._pool)