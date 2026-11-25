"""Immich v3 REST client, one method per endpoint use."""

import mimetypes
from datetime import UTC, datetime
from pathlib import Path

import httpx


class Immich:
    def __init__(self, url: str, api_key: str) -> None:
        self.http = httpx.AsyncClient(base_url=url, headers={"x-api-key": api_key}, timeout=600)

    async def _json(self, method: str, path: str, **kwargs):
        r = await self.http.request(method, path, **kwargs)
        if r.is_error:
            raise RuntimeError(f"Immich {method} {path}: {r.status_code} {r.text[:300]}")
        return r.json()

    async def tags(self) -> list[dict]:
        return await self._json("GET", "/tags")

    async def search(self, path: str, body: dict) -> list[dict]:
        return (await self._json("POST", path, json=body))["assets"]["items"]

    async def asset(self, asset_id: str) -> dict:
        return await self._json("GET", f"/assets/{asset_id}")

    async def download(self, path: str, params: dict, dest: Path) -> None:
        async with self.http.stream("GET", path, params=params) as r:
            if r.is_error:
                raise RuntimeError(f"Immich GET {path}: {r.status_code}")
            with dest.open("wb") as f:
                async for chunk in r.aiter_bytes():
                    f.write(chunk)

    async def upload(self, path: Path) -> str:
        filename = path.name
        now = datetime.now(UTC).isoformat()
        mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        with path.open("rb") as f:
            result = await self._json(
                "POST",
                "/assets",
                data={"fileCreatedAt": now, "fileModifiedAt": now, "filename": filename},
                files={"assetData": (filename, f, mime)},
            )
        return result["id"]

    async def describe(self, asset_id: str, description: str) -> None:
        await self._json("PUT", f"/assets/{asset_id}", json={"description": description})

    async def album(self, name: str) -> str:
        for album in await self._json("GET", "/albums"):
            if album["albumName"] == name:
                return album["id"]
        return (await self._json("POST", "/albums", json={"albumName": name}))["id"]

    async def add_to_album(self, album_id: str, asset_ids: list[str]) -> None:
        results = await self._json("PUT", f"/albums/{album_id}/assets", json={"ids": asset_ids})
        if failed := [r for r in results if not r["success"]]:
            detail = ", ".join(f"{r['id']}: {r.get('error')}" for r in failed)
            raise RuntimeError(f"Immich refused album additions: {detail}")

    async def tag(self, asset_ids: list[str], names: list[str]) -> None:
        """Upsert tags by full path (used/2026-W48 creates the parent too) and assign them."""
        upserted = await self._json("PUT", "/tags", json={"tags": names})
        ids = [t["id"] for t in upserted if t["value"] in names]
        await self._json("PUT", "/tags/assets", json={"assetIds": asset_ids, "tagIds": ids})
