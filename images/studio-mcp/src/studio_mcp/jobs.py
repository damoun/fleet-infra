"""In-memory job registry with a single background worker."""

import asyncio
import logging
import tempfile
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path

log = logging.getLogger("studio-mcp")


class Jobs:
    def __init__(self, work_dir: Path) -> None:
        self._work_dir = work_dir
        self._jobs: dict[str, dict] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker: asyncio.Task | None = None

    def submit(self, body: Callable[[Path], Awaitable[list[str]]]) -> str:
        if self._worker is None:
            self._worker = asyncio.create_task(self._loop())
        job_id = uuid.uuid4().hex[:12]
        self._jobs[job_id] = {"status": "queued"}
        self._queue.put_nowait((job_id, body))
        return job_id

    def status(self, job_id: str) -> dict:
        return self._jobs.get(job_id, {"status": "unknown"})

    async def _loop(self) -> None:
        while True:
            job_id, body = await self._queue.get()
            self._jobs[job_id] = {"status": "running"}
            try:
                with tempfile.TemporaryDirectory(
                    prefix=f"{job_id}-", dir=self._work_dir, ignore_cleanup_errors=True
                ) as work:
                    asset_ids = await body(Path(work))
                self._jobs[job_id] = {"status": "done", "asset_ids": asset_ids}
            except Exception as e:
                log.exception("job %s failed", job_id)
                self._jobs[job_id] = {"status": "failed", "error": f"{type(e).__name__}: {e}"}
