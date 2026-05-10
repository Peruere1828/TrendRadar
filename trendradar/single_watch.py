# coding=utf-8
"""
Single-user URL watcher.

This mode is intended for one-user-per-container deployments. It monitors one
configured source URL, filters new articles by topic keywords, fetches article
content, and sends a focused email notification.
"""

import hashlib
import html
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import urljoin, urlparse

import requests

from trendradar.ai.client import AIClient
from trendradar.crawler.article_content import ArticleContentFetcher
from trendradar.crawler.people_cn import PeopleCrawler
from trendradar.crawler.rss import RSSFeedConfig, RSSFetcher
from trendradar.notification.senders import send_to_email
from trendradar.storage.base import RSSData
from trendradar.utils.time import DEFAULT_TIMEZONE, get_configured_time


@dataclass
class WatchArticle:
    title: str
    url: str
    source_name: str = ""
    published_at: str = ""
    summary: str = ""

    @property
    def identity(self) -> str:
        key = self.url or self.title
        return hashlib.sha256(key.encode("utf-8")).hexdigest()


@dataclass
class SingleWatchConfig:
    watch_url: str
    keywords: List[str]
    email_from: str
    email_password: str
    email_to: str
    smtp_server: str = ""
    smtp_port: str = ""
    source_name: str = "Watch Source"
    data_dir: str = "output"
    state_file: str = ""
    timezone: str = DEFAULT_TIMEZONE
    max_items: int = 30
    max_content_chars: int = 8000
    notify_on_first_run: bool = True
    use_jina: bool = True
    jina_api_key: str = ""
    timeout: int = 30
    check_interval: int = 1800
    config_file: str = ""
    ai_summary_enabled: bool = True
    ai_summary_max_input_chars: int = 6000
    ai_summary_max_tokens: int = 700
    ai_config: Optional[Dict] = None


def load_single_watch_config(base_config: Optional[Dict] = None) -> SingleWatchConfig:
    base_config = base_config or {}

    data_dir = _env("STORAGE_DATA_DIR") or base_config.get("STORAGE", {}).get("LOCAL", {}).get("DATA_DIR", "output")
    config_file = _env("SINGLE_WATCH_CONFIG_FILE") or str(Path(data_dir) / "single_watch" / "config.json")
    saved_config = _load_saved_config(config_file)

    watch_url = _config_str("WATCH_URL", saved_config, "watch_url")
    keywords = _split_keywords(_config_str("WATCH_KEYWORDS", saved_config, "keywords") or _env("WATCH_TOPIC"))
    email_from = _env("EMAIL_FROM") or base_config.get("EMAIL_FROM", "")
    email_password = _env("EMAIL_PASSWORD") or base_config.get("EMAIL_PASSWORD", "")
    email_to = _config_str("EMAIL_TO", saved_config, "email_to") or base_config.get("EMAIL_TO", "")
    timezone = _env("TIMEZONE") or base_config.get("TIMEZONE", DEFAULT_TIMEZONE)
    base_ai_config = base_config.get("AI", {})

    return SingleWatchConfig(
        watch_url=watch_url,
        keywords=keywords,
        email_from=email_from,
        email_password=email_password,
        email_to=email_to,
        smtp_server=_env("EMAIL_SMTP_SERVER") or base_config.get("EMAIL_SMTP_SERVER", ""),
        smtp_port=_env("EMAIL_SMTP_PORT") or base_config.get("EMAIL_SMTP_PORT", ""),
        source_name=_config_str("WATCH_SOURCE_NAME", saved_config, "source_name") or "Watch Source",
        data_dir=data_dir,
        state_file=_env("WATCH_STATE_FILE") or str(Path(data_dir) / "single_watch" / "state.json"),
        timezone=timezone,
        max_items=_config_int("WATCH_MAX_ITEMS", saved_config, "max_items", 30),
        max_content_chars=_config_int("WATCH_MAX_CONTENT_CHARS", saved_config, "max_content_chars", 8000),
        notify_on_first_run=_config_bool("WATCH_NOTIFY_ON_FIRST_RUN", saved_config, "notify_on_first_run", True),
        use_jina=_config_bool("WATCH_USE_JINA", saved_config, "use_jina", True),
        jina_api_key=_env("JINA_API_KEY"),
        timeout=_config_int("WATCH_TIMEOUT", saved_config, "timeout", 30),
        check_interval=_config_int("CHECK_INTERVAL", saved_config, "check_interval", _env_int("WATCH_CHECK_INTERVAL", 1800)),
        config_file=config_file,
        ai_summary_enabled=_config_bool("WATCH_AI_SUMMARY_ENABLED", saved_config, "ai_summary_enabled", True),
        ai_summary_max_input_chars=_config_int(
            "WATCH_AI_SUMMARY_MAX_INPUT_CHARS",
            saved_config,
            "ai_summary_max_input_chars",
            6000,
        ),
        ai_summary_max_tokens=_config_int("WATCH_AI_SUMMARY_MAX_TOKENS", saved_config, "ai_summary_max_tokens", 700),
        ai_config={
            "MODEL": _env("WATCH_AI_MODEL") or _env("AI_MODEL") or base_ai_config.get("MODEL", "deepseek/deepseek-chat"),
            "API_KEY": _env("AI_API_KEY") or base_ai_config.get("API_KEY", ""),
            "API_BASE": _env("AI_API_BASE") or base_ai_config.get("API_BASE", ""),
            "TIMEOUT": _env_int("AI_TIMEOUT", base_ai_config.get("TIMEOUT", 120)),
            "TEMPERATURE": float(_env("WATCH_AI_TEMPERATURE") or base_ai_config.get("TEMPERATURE", 0.2)),
            "MAX_TOKENS": _env_int("WATCH_AI_SUMMARY_MAX_TOKENS", 700),
            "NUM_RETRIES": base_ai_config.get("NUM_RETRIES", 2),
            "FALLBACK_MODELS": base_ai_config.get("FALLBACK_MODELS", []),
        },
    )


class SingleWatcher:
    def __init__(self, config: SingleWatchConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "TrendRadar/6.6 SingleWatcher",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        self.content_fetcher = ArticleContentFetcher(
            jina_api_key=config.jina_api_key,
            timeout=config.timeout,
            max_chars=config.max_content_chars,
            use_jina=config.use_jina,
        )
        self.ai_client = self._build_ai_client()

    def run_once(self) -> bool:
        self._validate_config()
        state = self._load_state()
        articles = self.fetch_articles()
        if not articles:
            print("[single-watch] No articles found.")
            return False

        first_run = not state.get("initialized")
        seen = set(state.get("seen", []))

        new_articles = [item for item in articles if item.identity not in seen]
        if first_run and not self.config.notify_on_first_run:
            self._save_state(articles, state)
            print("[single-watch] First run initialized without notification.")
            return False

        matched = [item for item in new_articles if self._matches_keywords(item)]
        if not matched:
            self._save_state(articles, state)
            print(f"[single-watch] No keyword matches. New={len(new_articles)}")
            return False

        enriched = self._fetch_contents(matched)
        html_path = self._write_email_html(enriched)
        ok = send_to_email(
            from_email=self.config.email_from,
            password=self.config.email_password,
            to_email=self.config.email_to,
            report_type=f"{self.config.source_name} 新增相关文章",
            html_file_path=html_path,
            custom_smtp_server=self.config.smtp_server,
            custom_smtp_port=self.config.smtp_port,
            get_time_func=lambda: get_configured_time(self.config.timezone),
        )

        if ok:
            self._save_state(articles, state)
        return ok

    def fetch_articles(self) -> List[WatchArticle]:
        if self._is_people_source(self.config.watch_url):
            return self._fetch_people_articles()
        if self._looks_like_feed(self.config.watch_url):
            return self._fetch_rss_articles()
        feed_url = self._discover_feed_url(self.config.watch_url)
        if feed_url:
            print(f"[single-watch] Discovered feed: {feed_url}")
            return self._fetch_rss_articles(feed_url)
        return self._fetch_page_links()

    def _fetch_people_articles(self) -> List[WatchArticle]:
        feed_ids = self._people_feed_ids(self.config.watch_url)
        crawler = PeopleCrawler(max_items=self.config.max_items)
        data = crawler.fetch_all(feed_ids)
        return self._rss_data_to_articles(data)

    def _fetch_rss_articles(self, feed_url: Optional[str] = None) -> List[WatchArticle]:
        url = feed_url or self.config.watch_url
        fetcher = RSSFetcher(
            feeds=[
                RSSFeedConfig(
                    id="single-watch",
                    name=self.config.source_name,
                    url=url,
                    max_items=self.config.max_items,
                    enabled=True,
                )
            ],
            timeout=self.config.timeout,
            timezone=self.config.timezone,
        )
        data = fetcher.fetch_all()
        return self._rss_data_to_articles(data)

    def _fetch_page_links(self) -> List[WatchArticle]:
        response = self.session.get(self.config.watch_url, timeout=self.config.timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"
        base_url = response.url
        links = []
        seen_urls = set()

        for match in re.finditer(r'(?is)<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', response.text):
            href = html.unescape(match.group(1)).strip()
            title = self._clean_text(match.group(2))
            if not href or href.startswith(("#", "javascript:", "mailto:")):
                continue
            url = urljoin(base_url, href)
            if url in seen_urls or not self._same_site(base_url, url):
                continue
            if len(title) < 6:
                continue
            seen_urls.add(url)
            links.append(WatchArticle(title=title, url=url, source_name=self.config.source_name))
            if len(links) >= self.config.max_items:
                break

        print(f"[single-watch] Extracted {len(links)} links from page.")
        return links

    def _fetch_contents(self, articles: List[WatchArticle]) -> List[Dict]:
        enriched = []
        for article in articles:
            content = self.content_fetcher.fetch(article.url, article.title)
            article_content = content.content if content.success else ""
            summary = self._summarize_article(article, article_content) if article_content else ""
            enriched.append({
                "article": article,
                "content": article_content,
                "ai_summary": summary,
                "content_error": content.error,
                "content_source": content.source,
            })
            status = "ok" if content.success else f"failed: {content.error}"
            if summary:
                status += ", summarized"
            print(f"[single-watch] Content {status} - {article.title}")
        return enriched

    def _build_ai_client(self) -> Optional[AIClient]:
        if not self.config.ai_summary_enabled:
            return None

        ai_config = self.config.ai_config or {}
        if not ai_config.get("API_KEY"):
            print("[single-watch] AI summary skipped: AI_API_KEY not configured.")
            return None

        try:
            client = AIClient(ai_config)
            valid, message = client.validate_config()
            if not valid:
                print(f"[single-watch] AI summary skipped: {message}")
                return None
            return client
        except Exception as e:
            print(f"[single-watch] AI summary unavailable: {e}")
            return None

    def _summarize_article(self, article: WatchArticle, content: str) -> str:
        if not self.ai_client:
            return ""

        max_chars = max(500, self.config.ai_summary_max_input_chars)
        excerpt = content[:max_chars]
        keywords = ", ".join(self.config.keywords) if self.config.keywords else "用户关注主题"
        messages = [
            {
                "role": "system",
                "content": (
                    "你是新闻监控助手。请只依据用户提供的文章正文做摘要，"
                    "不要补充正文没有的信息。输出中文，简洁、可直接放入邮件。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"关注主题词：{keywords}\n"
                    f"文章标题：{article.title}\n"
                    f"文章链接：{article.url}\n\n"
                    "请完成：\n"
                    "1. 用 2-4 句话概括文章核心内容。\n"
                    "2. 如果文章与关注主题词有关，说明关联点；如果关联较弱，也如实说明。\n"
                    "3. 不要输出 Markdown 标题。\n\n"
                    f"正文：\n{excerpt}"
                ),
            },
        ]

        try:
            summary = self.ai_client.chat(
                messages,
                temperature=0.2,
                max_tokens=self.config.ai_summary_max_tokens,
            )
            return summary.strip()
        except Exception as e:
            print(f"[single-watch] AI summary failed - {article.title}: {e}")
            return ""

    def _matches_keywords(self, article: WatchArticle) -> bool:
        haystack = f"{article.title}\n{article.summary}".lower()
        return any(keyword.lower() in haystack for keyword in self.config.keywords)

    def _write_email_html(self, enriched: List[Dict]) -> str:
        now = get_configured_time(self.config.timezone)
        date_dir = Path(self.config.data_dir) / "single_watch" / now.strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        path = date_dir / f"single_watch_{now.strftime('%H-%M-%S')}.html"

        keyword_text = ", ".join(self.config.keywords)
        parts = [
            "<!DOCTYPE html><html><head><meta charset='UTF-8'>",
            "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.6;color:#222}"
            "a{color:#0b57d0}.article{border-top:1px solid #ddd;padding:18px 0}"
            ".meta{color:#666;font-size:13px}.content{white-space:pre-wrap;background:#f7f7f7;padding:12px;border-radius:6px}</style>",
            "</head><body>",
            f"<h2>{html.escape(self.config.source_name)} 新增相关文章</h2>",
            f"<p class='meta'>主题词：{html.escape(keyword_text)} | 生成时间：{html.escape(now.strftime('%Y-%m-%d %H:%M:%S'))}</p>",
            f"<p>本次发现 {len(enriched)} 篇新增相关文章。</p>",
        ]

        for index, item in enumerate(enriched, 1):
            article = item["article"]
            content = item.get("content") or f"正文抓取失败：{item.get('content_error', 'unknown error')}"
            ai_summary = item.get("ai_summary", "")
            parts.extend([
                "<div class='article'>",
                f"<h3>{index}. <a href='{html.escape(article.url)}'>{html.escape(article.title)}</a></h3>",
                f"<p class='meta'>来源：{html.escape(article.source_name or self.config.source_name)}"
                f"{' | 发布时间：' + html.escape(article.published_at) if article.published_at else ''}"
                f" | 正文来源：{html.escape(item.get('content_source') or 'none')}</p>",
            ])
            if ai_summary:
                parts.extend([
                    "<h4>AI 摘要</h4>",
                    f"<div class='content'>{html.escape(ai_summary)}</div>",
                    "<h4>正文摘录</h4>",
                ])
            else:
                parts.append("<h4>正文摘录</h4>")
            parts.extend([
                f"<div class='content'>{html.escape(content)}</div>",
                "</div>",
            ])

        parts.append("</body></html>")
        path.write_text("\n".join(parts), encoding="utf-8")
        return str(path)

    def _load_state(self) -> Dict:
        path = Path(self.config.state_file)
        if not path.exists():
            return {"initialized": False, "seen": []}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {"initialized": False, "seen": []}

    def _save_state(self, articles: Iterable[WatchArticle], previous_state: Dict) -> None:
        seen = set(previous_state.get("seen", []))
        seen.update(article.identity for article in articles)
        payload = {
            "initialized": True,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "watch_url": self.config.watch_url,
            "seen": sorted(seen),
        }
        path = Path(self.config.state_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _validate_config(self) -> None:
        missing = []
        if not self.config.watch_url:
            missing.append("WATCH_URL")
        if not self.config.keywords:
            missing.append("WATCH_KEYWORDS")
        if not self.config.email_from:
            missing.append("EMAIL_FROM")
        if not self.config.email_password:
            missing.append("EMAIL_PASSWORD")
        if not self.config.email_to:
            missing.append("EMAIL_TO")
        if missing:
            raise ValueError(f"single-watch missing required config: {', '.join(missing)}")

    @staticmethod
    def _rss_data_to_articles(data: RSSData) -> List[WatchArticle]:
        articles = []
        for feed_id, items in data.items.items():
            source_name = data.id_to_name.get(feed_id, feed_id)
            for item in items:
                articles.append(WatchArticle(
                    title=item.title,
                    url=item.url,
                    source_name=source_name,
                    published_at=item.published_at,
                    summary=item.summary,
                ))
        return articles

    @staticmethod
    def _looks_like_feed(url: str) -> bool:
        lower = url.lower()
        return lower.endswith((".xml", ".rss", ".atom", ".json")) or "feed" in lower or "rss" in lower

    def _discover_feed_url(self, url: str) -> Optional[str]:
        try:
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"
            for match in re.finditer(r'(?is)<link\b[^>]*>', response.text):
                tag = match.group(0)
                if not re.search(r'type=["\']application/(rss\+xml|atom\+xml|feed\+json|json)', tag, re.I):
                    continue
                href_match = re.search(r'href=["\']([^"\']+)["\']', tag, re.I)
                if href_match:
                    return urljoin(response.url, html.unescape(href_match.group(1)))
        except Exception as e:
            print(f"[single-watch] Feed discovery failed: {e}")
        return None

    @staticmethod
    def _is_people_source(url: str) -> bool:
        return "people.cn" in urlparse(url).netloc.lower()

    @staticmethod
    def _people_feed_ids(url: str) -> List[str]:
        lower = url.lower()
        feed_ids = []
        if "finance" in lower or "money" in lower:
            feed_ids.append("people-finance")
        if "scitech" in lower or "tech" in lower or "kpzg" in lower:
            feed_ids.append("people-scitech")
        if "politics" in lower:
            feed_ids.append("people-politics")
        return feed_ids or ["people-finance", "people-scitech"]

    @staticmethod
    def _same_site(base_url: str, candidate_url: str) -> bool:
        base_host = urlparse(base_url).netloc.lower()
        candidate_host = urlparse(candidate_url).netloc.lower()
        return base_host == candidate_host or candidate_host.endswith("." + base_host)

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"(?s)<[^>]+>", " ", text)
        text = html.unescape(text)
        return re.sub(r"\s+", " ", text).strip()


def run_single_watch(base_config: Optional[Dict] = None) -> bool:
    config = load_single_watch_config(base_config)
    watcher = SingleWatcher(config)
    return watcher.run_once()


def run_single_watch_loop(base_config: Optional[Dict] = None) -> None:
    while True:
        config = load_single_watch_config(base_config)
        watcher = SingleWatcher(config)
        try:
            watcher.run_once()
        except Exception as e:
            print(f"[single-watch] Run failed: {e}")
        print(f"[single-watch] Sleeping {config.check_interval} seconds...")
        time.sleep(max(30, config.check_interval))


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def _env_int(name: str, default: int) -> int:
    value = _env(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = _env(name).lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


def _load_saved_config(path: str) -> Dict:
    config_path = Path(path)
    if not config_path.exists():
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"[single-watch] Failed to load form config {path}: {e}")
        return {}


def _config_str(env_name: str, saved_config: Dict, saved_key: str) -> str:
    env_value = _env(env_name)
    if env_value:
        return env_value
    value = saved_config.get(saved_key, "")
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value).strip() if value is not None else ""


def _config_int(env_name: str, saved_config: Dict, saved_key: str, default: int) -> int:
    env_value = _env(env_name)
    if env_value:
        return _env_int(env_name, default)
    value = saved_config.get(saved_key)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _config_bool(env_name: str, saved_config: Dict, saved_key: str, default: bool) -> bool:
    env_value = _env(env_name)
    if env_value:
        return _env_bool(env_name, default)
    value = saved_config.get(saved_key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


def _split_keywords(value: str) -> List[str]:
    return [item.strip() for item in re.split(r"[,;，；\n]+", value or "") if item.strip()]
