# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Protocol, Sequence

from .models import ContentItem


class ContentParser(Protocol):
    """Parses raw HTML into a sequence of content fragments."""

    def parse(self, html_content: str) -> Sequence[ContentItem]:
        ...
