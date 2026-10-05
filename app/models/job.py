"""Job model."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Job:
    """Satu job pengiriman pesan ke NGL.

    Attributes:
        id: UUID unik untuk job.
        username: Target username.
        message: Pesan yang akan dikirim.
        device_id: Device ID (UUID) untuk request ini.
        attempts: Jumlah percobaan.
        created_at: Timestamp pembuatan.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    message: str = ""
    device_id: str = ""
    attempts: int = 0
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def increment_attempt(self) -> int:
        """Naikkan counter attempts."""
        self.attempts += 1
        return self.attempts