from dataclasses import dataclass
from typing import Any

import aiohttp


@dataclass
class HttpResponse:
    status: int
    data: Any
    headers: dict
    ok: bool


class HttpClient:
    def __init__(self, timeout: int = 20):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    def start(self):
        self._session = aiohttp.ClientSession(timeout=self.timeout)

    async def close(self):
        if self._session:
            await self._session.close()

    async def _read_response(self, resp: aiohttp.ClientResponse) -> Any:
        if "json" in resp.content_type:
            return await resp.json()
        return await resp.text()

    async def get(
        self, url: str, params: dict | None = None, headers: dict | None = None
    ) -> HttpResponse:
        if self._session is None:
            raise RuntimeError("HttpClient not started. Call start() first.")

        async with self._session.get(url, params=params, headers=headers) as resp:
            data = await self._read_response(resp)
            return HttpResponse(
                status=resp.status,
                data=data,
                headers=dict(resp.headers),
                ok=resp.status < 400,
            )

    # assumes we send only json or None
    async def post(
        self, url: str, json: dict | None = None, headers: dict | None = None
    ) -> HttpResponse:
        if self._session is None:
            raise RuntimeError("HttpClient not started. Call start() first.")

        async with self._session.post(url, json=json, headers=headers) as resp:
            data = await self._read_response(resp)
            return HttpResponse(
                status=resp.status,
                data=data,
                headers=dict(resp.headers),
                ok=resp.status < 400,
            )

    def get_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError("HttpClient not started. Call start() first.")
        return self._session
