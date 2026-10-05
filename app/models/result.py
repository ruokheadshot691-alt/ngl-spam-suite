"""Result model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Result:
    """Hasil dari satu job.

    Attributes:
        job_id: ID job terkait.
        username: Target username.
        message: Pesan yang dikirim.
        status_code: HTTP status code (0 kalau connection error).
        success: True kalau berhasil (2xx).
        latency_ms: Latensi request dalam milidetik.
        error: Pesan error kalau gagal.
        timestamp: Waktu penyelesaian.
        attempts: Jumlah attempts yang dipakai.
    """

    job_id: str
    username: str
    message: str
    status_code: int
    success: bool
    latency_ms: float
    error: Optional[str] = None
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    attempts: int = 1

    def to_dict(self) -> dict:
        """Konversi ke dict (JSON-serializable)."""
        return {
            "job_id": self.job_id,
            "username": self.username,
            "message": self.message,
            "status_code": self.status_code,
            "success": self.success,
            "latency_ms": round(self.latency_ms, 1),
            "error": self.error,
            "attempts": self.attempts,
            "timestamp": self.timestamp.isoformat(),
        }