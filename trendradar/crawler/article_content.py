# coding=utf-8
"""
Article content extraction.

The main TrendRadar pipeline mostly works with titles and summaries. This module
provides a reusable article-body fetcher for notification flows that need the
actual article text.
"""

import html
import re
import time
from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class ArticleContent:
    url: str
    title: str = ""
    content: str = ""
    source: str = ""
    success: bool = False
    error: str = ""


class ArticleContentFetcher:
    """Fetch and clean article body text.

    It prefers Jina Reader because many news pages are hard to parse reliably.
    If Jina fails, it falls back to a lightweight local HTML text extraction so
    the notification flow can still produce useful output.
    """

    JINA_READER_BASE = "https://r.jina.ai"

    def __init__(
        self,
        jina_api_key: str = "",
        timeout: int = 30,
        min_interval: float = 1.0,
        max_chars: int = 8000,
        use_jina: bool = True,
    ):
        self.jina_api_key = jina_api_key
        self.timeout = timeout
        self.min_interval = min_interval
        self.max_chars = max_chars
        self.use_jina = use_jina
        self._last_request_time = 0.0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "TrendRadar/6.6 ArticleContentFetcher",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })

    def fetch(self, url: str, title: str = "") -> ArticleContent:
        if not url or not url.startswith(("http://", "https://")):
            return ArticleContent(url=url, title=title, success=False, error="invalid url")

        if self.use_jina:
            result = self._fetch_with_jina(url, title)
            if result.success and result.content:
                return result

        return self._fetch_with_html(url, title)

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request_time = time.time()

    def _fetch_with_jina(self, url: str, title: str = "") -> ArticleContent:
        try:
            self._throttle()
            headers = {
                "Accept": "text/markdown",
                "X-Return-Format": "markdown",
                "X-No-Cache": "true",
            }
            if self.jina_api_key:
                headers["Authorization"] = f"Bearer {self.jina_api_key}"

            response = self.session.get(
                f"{self.JINA_READER_BASE}/{url}",
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            text = self._clean_markdown(response.text)
            return ArticleContent(
                url=url,
                title=title or self._extract_markdown_title(response.text),
                content=self._truncate(text),
                source="jina",
                success=bool(text),
            )
        except Exception as e:
            return ArticleContent(url=url, title=title, source="jina", error=str(e))

    def _fetch_with_html(self, url: str, title: str = "") -> ArticleContent:
        try:
            self._throttle()
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = self._detect_encoding(response)
            raw_html = response.text
            extracted_title = title or self._extract_html_title(raw_html)
            text = self._extract_html_text(raw_html)
            return ArticleContent(
                url=url,
                title=extracted_title,
                content=self._truncate(text),
                source="html",
                success=bool(text),
            )
        except Exception as e:
            return ArticleContent(url=url, title=title, source="html", error=str(e))

    def _truncate(self, text: str) -> str:
        text = text.strip()
        if self.max_chars > 0 and len(text) > self.max_chars:
            return text[: self.max_chars].rstrip() + "\n\n[正文已截断]"
        return text

    @staticmethod
    def _detect_encoding(response) -> str:
        content_type = response.headers.get("Content-Type", "")
        match = re.search(r"charset=([^\s;]+)", content_type, re.I)
        if match:
            return match.group(1)
        match = re.search(rb'<meta[^>]+charset=["\']?([^"\'>;\s]+)', response.content[:4096], re.I)
        if match:
            return match.group(1).decode("ascii", errors="ignore")
        return response.apparent_encoding or "utf-8"

    @staticmethod
    def _extract_html_title(raw_html: str) -> str:
        match = re.search(r"<title[^>]*>(.*?)</title>", raw_html, re.I | re.S)
        if not match:
            return ""
        return html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()

    @staticmethod
    def _extract_markdown_title(text: str) -> str:
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
            if line:
                return line[:120]
        return ""

    @staticmethod
    def _clean_markdown(text: str) -> str:
        text = text.replace("\r\n", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _extract_html_text(raw_html: str) -> str:
        raw_html = re.sub(r"(?is)<(script|style|noscript|svg|canvas).*?</\1>", " ", raw_html)
        raw_html = re.sub(r"(?is)<!--.*?-->", " ", raw_html)
        raw_html = re.sub(r"(?i)<\s*(br|p|div|section|article|li|h[1-6])[^>]*>", "\n", raw_html)
        text = re.sub(r"(?s)<[^>]+>", " ", raw_html)
        text = html.unescape(text)
        lines = []
        for line in text.splitlines():
            line = re.sub(r"\s+", " ", line).strip()
            if len(line) >= 12:
                lines.append(line)
        return "\n\n".join(lines).strip()
