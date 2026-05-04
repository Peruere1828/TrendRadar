# coding=utf-8
"""
人民网 Sitemap 爬虫

人民网 RSS 已废弃（停在 2025-06），改用 sitemap + 页面标题抓取。
Sitemap 提供今日文章 URL 和日期，再抓取每篇文章的 <title> 获取标题。
"""

import re
import time
import random
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional

import requests

from trendradar.storage.base import RSSItem, RSSData

SITEMAP_URLS = {
    "people-politics": "http://www.people.cn/sitemap/cn/politics/news_sitemap.xml",
    "people-finance": "http://www.people.cn/sitemap/cn/finance/news_sitemap.xml",
    "people-scitech": "http://www.people.cn/sitemap/cn/scitech/news_sitemap.xml",
}

FEED_NAMES = {
    "people-politics": "人民网·时政",
    "people-finance": "人民网·财经",
    "people-scitech": "人民网·科技",
}

NS = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
_SESSION = None


def _detect_encoding(resp) -> str:
    """Detect correct encoding — Content-Type header > meta charset > chardet > UTF-8."""
    ct = resp.headers.get("Content-Type", "")
    m = re.search(r"charset=([^\s;]+)", ct)
    if m:
        return m.group(1)
    m = re.search(rb'<meta[^>]+charset=["\']?([^"\'>;\s]+)', resp.content[:2048], re.IGNORECASE)
    if m:
        return m.group(1).decode("ascii")
    apparent = resp.apparent_encoding
    if apparent:
        return apparent
    return "utf-8"


def _get_session() -> requests.Session:
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
        _SESSION.headers.update({
            "User-Agent": "TrendRadar/2.0 PeopleCrawler",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
    return _SESSION


def _fetch_sitemap(url: str, timeout: int = 15) -> List[Dict]:
    resp = _get_session().get(url, timeout=timeout)
    resp.raise_for_status()
    resp.encoding = _detect_encoding(resp)
    root = ET.fromstring(resp.text)
    items = []
    for url_el in root.findall("ns:url", NS):
        loc = url_el.find("ns:loc", NS)
        lastmod = url_el.find("ns:lastmod", NS)
        if loc is not None and loc.text:
            items.append({
                "url": loc.text.strip(),
                "lastmod": lastmod.text.strip() if lastmod is not None and lastmod.text else "",
            })
    return items


def _extract_title(html: str) -> str:
    """Extract article title from 人民网 <title> tag.

    Format: '文章标题--频道名--人民网' → '文章标题'
    """
    match = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
    if not match:
        return ""
    raw = match.group(1).strip()
    return raw.split("--")[0].strip()


def _scrape_page(session: requests.Session, url: str, timeout: int = 10) -> Optional[str]:
    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
        resp.encoding = _detect_encoding(resp)
        title = _extract_title(resp.text)
        return title or None
    except Exception:
        return None


def _scrape_batch(
    url_items: List[Dict],
    max_workers: int = 4,
    request_delay: float = 1.5,
    timeout: int = 10,
) -> List[Dict]:
    """Scrape titles in parallel for a batch of article URLs."""
    results = []
    session = _get_session()

    def fetch_one(item: Dict, _index: int) -> Optional[Dict]:
        time.sleep(random.uniform(0.5, request_delay))
        title = _scrape_page(session, item["url"], timeout)
        if title:
            return {
                "title": title,
                "url": item["url"],
                "published_at": item.get("lastmod", ""),
            }
        return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_one, item, i): i for i, item in enumerate(url_items)}
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    return results


class PeopleCrawler:
    """人民网 sitemap crawler. Produces RSSData for integration with existing pipeline."""

    def __init__(
        self,
        max_items: int = 20,
        max_workers: int = 4,
        request_delay: float = 1.5,
        timeout: int = 10,
    ):
        self.max_items = max_items
        self.max_workers = max_workers
        self.request_delay = request_delay
        self.timeout = timeout

    def fetch_feed(self, feed_id: str) -> Optional[List[Dict]]:
        sitemap_url = SITEMAP_URLS.get(feed_id)
        if not sitemap_url:
            return None

        feed_name = FEED_NAMES.get(feed_id, feed_id)
        print(f"[人民网] 获取 {feed_name} sitemap...")

        try:
            url_items = _fetch_sitemap(sitemap_url, timeout=self.timeout)
        except Exception as e:
            print(f"[人民网] sitemap 获取失败 ({feed_name}): {e}")
            return None

        if not url_items:
            print(f"[人民网] sitemap 为空 ({feed_name})")
            return None

        url_items = url_items[:self.max_items]
        print(f"[人民网] {feed_name}: {len(url_items)} 个 URL，抓取标题中...")

        items = _scrape_batch(
            url_items,
            max_workers=self.max_workers,
            request_delay=self.request_delay,
            timeout=self.timeout,
        )

        for item in items:
            item["feed_id"] = feed_id
            item["feed_name"] = feed_name

        print(f"[人民网] {feed_name}: 成功 {len(items)}/{len(url_items)} 条")
        return items

    def fetch_all(self, feed_ids: List[str]) -> RSSData:
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        crawl_time = now.strftime("%H:%M")

        all_items: Dict[str, List[RSSItem]] = {}
        id_to_name: Dict[str, str] = {}
        failed_ids: List[str] = []

        for feed_id in feed_ids:
            try:
                item_dicts = self.fetch_feed(feed_id)
                if item_dicts is None:
                    failed_ids.append(feed_id)
                    continue

                rss_items = []
                for d in item_dicts:
                    rss_items.append(RSSItem(
                        title=d.get("title", ""),
                        feed_id=feed_id,
                        feed_name=FEED_NAMES.get(feed_id, feed_id),
                        url=d.get("url", ""),
                        published_at=d.get("published_at", ""),
                        crawl_time=crawl_time,
                    ))

                all_items[feed_id] = rss_items
                id_to_name[feed_id] = FEED_NAMES.get(feed_id, feed_id)

            except Exception as e:
                print(f"[人民网] {feed_id} 抓取异常: {e}")
                failed_ids.append(feed_id)

        return RSSData(
            date=date_str,
            crawl_time=crawl_time,
            items=all_items,
            id_to_name=id_to_name,
            failed_ids=failed_ids,
        )
