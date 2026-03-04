# -*- coding: utf-8 -*-
"""
HTTP 获取策略
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Mapping, MutableMapping, Optional, Protocol

logger = logging.getLogger(__name__)


@dataclass
class FetchRequest:
    """Parameters used for an HTTP fetch operation."""

    url: str
    method: str = "GET"
    headers: Mapping[str, str] | None = None
    timeout: float = 10.0
    allow_redirects: bool = True
    impersonate: Optional[str] = None
    params: Mapping[str, str] | None = None
    data: Mapping[str, str] | None = None
    cookies: Mapping[str, str] | None = None
    extras: MutableMapping[str, object] = field(default_factory=dict)


class FetchStrategy(Protocol):
    """Strategy interface for fetching raw content."""

    def fetch(self, request: FetchRequest) -> str:
        ...


class RequestsFetcher(FetchStrategy):
    """Default fetcher implemented with the `requests` library."""

    def fetch(self, request: FetchRequest) -> str:
        from requests import request as http_request

        response = http_request(
            method=request.method,
            url=request.url,
            headers=request.headers,
            timeout=request.timeout,
            allow_redirects=request.allow_redirects,
            params=request.params,
            data=request.data,
            cookies=request.cookies,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch content: {response.status_code}")
        response.encoding = response.encoding or "utf-8"
        return response.text


class CurlCffiFetcher(FetchStrategy):
    """Fetcher backed by curl_cffi for high-fidelity browser impersonation."""

    def fetch(self, request: FetchRequest) -> str:
        try:
            from curl_cffi import requests as curl_requests
        except ImportError as exc:
            raise RuntimeError("curl_cffi is required for this fetcher") from exc

        kwargs = {
            "headers": request.headers,
            "timeout": request.timeout,
            "allow_redirects": request.allow_redirects,
            "params": request.params,
            "data": request.data,
            "cookies": request.cookies,
        }
        impersonate = request.impersonate or request.extras.get("impersonate")
        if impersonate:
            kwargs["impersonate"] = impersonate

        response = curl_requests.request(
            method=request.method,
            url=request.url,
            **kwargs,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch content: {response.status_code}")
        response.encoding = response.encoding or "utf-8"
        return response.text
