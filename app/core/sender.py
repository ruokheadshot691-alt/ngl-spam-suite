"""Core HTTP sender — async single request ke NGL."""

from __future__ import annotations

import time
from typing import Optional

import httpx

from app.models.job import Job
from app.models.result import Result

NGL_ENDPOINT = "https://ngl.link/api/submit"
DEFAULT_TIMEOUT = 10.0
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class NGLSender:
    """Sender async untuk endpoint NGL.

    Attributes:
        endpoint: URL endpoint NGL.
        timeout: Timeout request.
        user_agent: User-Agent header.
    """

    def __init__(
        self,
        *,
        endpoint: str = NGL_ENDPOINT,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_UA,
    ) -> None:
        self.endpoint = endpoint
        self.timeout = timeout
        self.user_agent = user_agent
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "NGLSender":
        await self.open()
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.close()

    async def open(self) -> None:
        """Buka httpx.AsyncClient (lazy)."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "*/*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Origin": "https://ngl.link",
                    "Referer": "https://ngl.link/",
                },
            )

    async def close(self) -> None:
        """Tutup client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def send(
        self,
        job: Job,
        *,
        dry_run: bool = False,
        proxy: Optional[str] = None,
    ) -> Result:
        """Kirim satu job.

        Args:
            job: Job yang dikirim.
            dry_run: Kalau True, tidak benar-benar request.
            proxy: Proxy URL opsional.

        Returns:
            Result.
        """
        start = time.perf_counter()

        if dry_run:
            import asyncio
            import random
            await asyncio.sleep(random.uniform(0.05, 0.15))
            latency = (time.perf_counter() - start) * 1000
            return Result(
                job_id=job.id,
                username=job.username,
                message=job.message,
                status_code=200,
                success=True,
                latency_ms=latency,
                error=None,
                attempts=job.attempts or 1,
            )

        await self.open()
        assert self._client is not None

        data = {
            "username": job.username,
            "question": job.message,
            "deviceId": job.device_id,
            "gameSlug": "",
            "referrer": "",
        }

        try:
            kwargs: dict = {"data": data}
            if proxy:
                kwargs["proxy"] = proxy

            resp = await self._client.post(self.endpoint, **kwargs)
            latency = (time.perf_counter() - start) * 1000
            success = 200 <= resp.status_code < 300

            return Result(
                job_id=job.id,
                username=job.username,
                message=job.message,
                status_code=resp.status_code,
                success=success,
                latency_ms=latency,
                error=None if success else f"HTTP {resp.status_code}",
                attempts=job.attempts or 1,
            )
        except httpx.TimeoutException as e:
            latency = (time.perf_counter() - start) * 1000
            return Result(
                job_id=job.id,
                username=job.username,
                message=job.message,
                status_code=0,
                success=False,
                latency_ms=latency,
                error=f"Timeout: {e}",
                attempts=job.attempts or 1,
            )
        except httpx.HTTPError as e:
            latency = (time.perf_counter() - start) * 1000
            return Result(
                job_id=job.id,
                username=job.username,
                message=job.message,
                status_code=0,
                success=False,
                latency_ms=latency,
                error=f"HTTP error: {e}",
                attempts=job.attempts or 1,
            )
        except Exception as e:  # noqa: BLE001
            latency = (time.perf_counter() - start) * 1000
            return Result(
                job_id=job.id,
                username=job.username,
                message=job.message,
                status_code=0,
                success=False,
                latency_ms=latency,
                error=str(e),
                attempts=job.attempts or 1,
            )