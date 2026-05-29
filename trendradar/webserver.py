"""
TrendRadar Custom Web Server.

Replaces python -m http.server with a custom handler that:
- Serves static files from the output directory (existing behavior)
- Provides /my_interest page for natural-language interest management
- Provides API endpoints for interest CRUD and AI tag preview
"""

import json
import logging
import os
import sys
import traceback
from datetime import datetime, timezone, timedelta
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

import yaml

from trendradar.web_pages import (
    home_page,
    dashboard,
    platforms_page,
    rss_page,
    filter_page,
    notification_page,
    ai_page,
)

logging.basicConfig(level=logging.INFO, format="[WebServer] %(message)s")
logger = logging.getLogger(__name__)

# ---- Paths ----
OUTPUT_DIR = Path(os.environ.get("WEBSERVER_DIR", "/app/output")).resolve()
CONFIG_DIR = Path(os.environ.get("CONFIG_DIR", "/app/config")).resolve()
APP_DIR = Path(os.environ.get("APP_DIR", "/app")).resolve()
INTERESTS_FILE = CONFIG_DIR / "ai_interests.txt"
EXTRACT_PROMPT_FILE = CONFIG_DIR / "ai_filter" / "extract_prompt.txt"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
KEYWORDS_FILE = CONFIG_DIR / "frequency_words.txt"
VERSION_FILE = APP_DIR / "version"

# Ensure the app dir is importable
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# ---- AI Config from env ----
AI_MODEL = os.environ.get("AI_MODEL_WEBSERVER", os.environ.get("AI_MODEL", "openai/deepseek-v4"))
AI_API_KEY = os.environ.get("AI_API_KEY", "")
AI_API_BASE = os.environ.get("AI_API_BASE", "")
AI_TIMEOUT = int(os.environ.get("AI_TIMEOUT", "120"))
AI_MAX_TOKENS = int(os.environ.get("AI_MAX_TOKENS", "2000"))
AI_TEMPERATURE = float(os.environ.get("AI_TEMPERATURE", "0.3"))

# ---- HTML Page ----
MY_INTEREST_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>My Interest - 智汇</title>
<style>
:root {
  --bg: #1a1a2e; --card: #16213e; --card2: #0f3460;
  --text: #e0e0e0; --text2: #a0a0b0; --accent: #e94560;
  --green: #00b894; --blue: #0984e3; --border: #2d3748;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg); color: var(--text); min-height: 100vh; padding: 20px;
}
.container { max-width: 900px; margin: 0 auto; }
h1 { font-size: 1.5rem; margin-bottom: 8px; }
.subtitle { color: var(--text2); font-size: 0.9rem; margin-bottom: 20px; }
.card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 10px; padding: 20px; margin-bottom: 20px;
}
.card h2 { font-size: 1.1rem; margin-bottom: 12px; }
textarea {
  width: 100%; min-height: 250px; background: var(--bg);
  color: var(--text); border: 1px solid var(--border);
  border-radius: 8px; padding: 14px; font-size: 0.92rem;
  line-height: 1.6; font-family: inherit; resize: vertical;
}
textarea:focus { outline: none; border-color: var(--accent); }
.btn-row { display: flex; gap: 10px; margin-top: 14px; flex-wrap: wrap; }
.btn {
  padding: 10px 22px; border: none; border-radius: 8px;
  font-size: 0.92rem; cursor: pointer; font-weight: 600;
  transition: all 0.2s; display: inline-flex; align-items: center; gap: 6px;
}
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover { filter: brightness(1.2); }
.btn-secondary { background: var(--blue); color: #fff; }
.btn-secondary:hover { filter: brightness(1.2); }
.btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }
.btn-outline:hover { background: var(--card2); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.status {
  margin-top: 12px; padding: 10px 14px; border-radius: 6px;
  font-size: 0.88rem; display: none;
}
.status.success { background: rgba(0,184,148,0.15); color: var(--green); display: block; }
.status.error { background: rgba(233,69,96,0.15); color: #ff6b81; display: block; }
.status.info { background: rgba(9,132,227,0.15); color: var(--blue); display: block; }
.tag-list { margin-top: 16px; }
.tag-item {
  background: var(--card2); border: 1px solid var(--border);
  border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;
  display: flex; align-items: flex-start; gap: 10px;
  cursor: grab; transition: all 0.15s;
}
.tag-item.dragging { opacity: 0.5; }
.tag-item.drag-over { border-color: var(--accent); }
.tag-item .drag-handle { color: var(--text2); font-size: 1.2rem; cursor: grab; user-select: none; margin-top: 2px; }
.tag-item .tag-info { flex: 1; }
.tag-item .tag-name { font-weight: 700; margin-bottom: 4px; }
.tag-item .tag-desc { font-size: 0.85rem; color: var(--text2); line-height: 1.4; }
.tag-item .tag-actions { display: flex; gap: 6px; flex-shrink: 0; }
.tag-item .tag-actions button {
  padding: 5px 10px; font-size: 0.78rem; border-radius: 5px;
  border: 1px solid var(--border); background: transparent;
  color: var(--text2); cursor: pointer; white-space: nowrap;
}
.tag-item .tag-actions button:hover { background: var(--card); color: #fff; }
.news-sample { margin-top: 20px; }
.news-item {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: 6px; padding: 10px 14px; margin-bottom: 6px; font-size: 0.87rem;
}
.news-item .news-title {}
.news-item .news-meta { color: var(--text2); font-size: 0.78rem; margin-top: 4px; }
.news-item .news-score { color: var(--green); }
.spinner {
  display: inline-block; width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff; border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.empty-state { text-align: center; padding: 40px; color: var(--text2); }
</style>
</head>
<body>
<div class="container">
  <h1>我的兴趣配置</h1>
  <p class="subtitle">用自然语言描述你关注的话题，AI 自动提取标签并分类新闻。修改后将在下次调度运行时生效。</p>

  <div class="card">
    <h2>兴趣描述</h2>
    <textarea id="interestsInput" placeholder="描述你关注的话题..."></textarea>
    <div class="btn-row">
      <button class="btn btn-primary" id="btnSave" onclick="saveInterests()">保存</button>
      <button class="btn btn-secondary" id="btnPreview" onclick="previewTags()">AI 预览标签</button>
      <button class="btn btn-outline" id="btnReset" onclick="loadInterests()">重新加载</button>
    </div>
    <div id="status" class="status"></div>
  </div>

  <div class="card" id="tagsCard" style="display:none;">
    <h2>AI 提取的标签 <span style="font-weight:400;font-size:0.8rem;color:var(--text2);">（拖拽调整优先级）</span></h2>
    <div class="tag-list" id="tagList"></div>
    <div class="news-sample" id="newsSample" style="display:none;">
      <h2 style="margin-bottom:12px;">新闻样本：<span id="newsSampleTitle"></span></h2>
      <div id="newsList"></div>
    </div>
  </div>
</div>

<script>
let currentTags = [];
let draggedIdx = null;

function $(id) { return document.getElementById(id); }

function showStatus(msg, type) {
  const el = $('status');
  el.textContent = msg; el.className = 'status ' + type;
  setTimeout(() => { if (el.textContent === msg) el.className = 'status'; }, 5000);
}

async function loadInterests() {
  try {
    const r = await fetch('/api/interests');
    const d = await r.json();
    $('interestsInput').value = d.content || '';
  } catch(e) {
    showStatus('加载失败： ' + e.message, 'error');
  }
}

async function saveInterests() {
  const btn = $('btnSave');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Saving...';
  try {
    const content = $('interestsInput').value;
    const r = await fetch('/api/interests', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({content}),
    });
    const d = await r.json();
    if (d.success) {
      showStatus('已保存，将在下次运行时生效。', 'success');
    } else {
      showStatus('保存失败：' + (d.error || '未知错误'), 'error');
    }
  } catch(e) {
    showStatus('请求失败：' + e.message, 'error');
  } finally {
    btn.disabled = false; btn.innerHTML = 'Save';
  }
}

async function previewTags() {
  const btn = $('btnPreview');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Extracting...';
  $('newsSample').style.display = 'none';
  try {
    const content = $('interestsInput').value;
    if (!content.trim()) { showStatus('请先输入兴趣描述', 'error'); return; }
    const r = await fetch('/api/interests/preview', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({content}),
    });
    const d = await r.json();
    if (d.error) {
      showStatus('AI 提取失败：' + d.error, 'error');
    } else {
      currentTags = d.tags || [];
      renderTags();
      $('tagsCard').style.display = 'block';
      showStatus('AI 已提取 ' + currentTags.length + ' 个标签', 'success');
    }
  } catch(e) {
    showStatus('请求失败：' + e.message, 'error');
  } finally {
    btn.disabled = false; btn.innerHTML = 'AI Preview Tags';
  }
}

function renderTags() {
  const list = $('tagList');
  list.innerHTML = currentTags.map((t, i) =>
    '<div class="tag-item" draggable="true" data-idx="' + i + '"' +
    ' ondragstart="handleDragStart(event,' + i + ')"' +
    ' ondragover="handleDragOver(event)"' +
    ' ondragenter="handleDragEnter(event,' + i + ')"' +
    ' ondragend="handleDragEnd(event)"' +
    ' ondragleave="handleDragLeave(event)"' +
    ' ondrop="handleDrop(event,' + i + ')">' +
    '<span class="drag-handle">&#9776;</span>' +
    '<div class="tag-info">' +
    '<div class="tag-name">' + (i + 1) + '. ' + escHtml(t.tag) + '</div>' +
    '<div class="tag-desc">' + escHtml(t.description || '') + '</div>' +
    '</div>' +
    '<div class="tag-actions">' +
    '<button onclick="previewNews(' + i + ')">查看样本</button>' +
    '</div></div>'
  ).join('');
}

function handleDragStart(e, idx) {
  draggedIdx = idx;
  e.target.classList.add('dragging');
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('text/plain', idx.toString());
}
function handleDragOver(e) { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; }
function handleDragEnter(e, idx) {
  e.preventDefault();
  const el = e.target.closest('.tag-item');
  if (el) el.classList.add('drag-over');
}
function handleDragLeave(e) {
  const el = e.target.closest('.tag-item');
  if (el) el.classList.remove('drag-over');
}
function handleDragEnd(e) {
  e.target.classList.remove('dragging');
  document.querySelectorAll('.tag-item').forEach(el => el.classList.remove('drag-over'));
  draggedIdx = null;
}
function handleDrop(e, targetIdx) {
  e.preventDefault();
  const el = e.target.closest('.tag-item');
  if (el) el.classList.remove('drag-over');
  if (draggedIdx === null || draggedIdx === targetIdx) return;
  const [moved] = currentTags.splice(draggedIdx, 1);
  currentTags.splice(targetIdx, 0, moved);
  renderTags();
}

async function previewNews(tagIdx) {
  const tag = currentTags[tagIdx];
  $('newsSample').style.display = 'block';
  $('newsSampleTitle').textContent = '"' + tag.tag + '"';
  $('newsList').innerHTML = '<div class="empty-state"><span class="spinner"></span> AI 分类中...</div>';
  try {
    const content = $('interestsInput').value;
    const r = await fetch('/api/interests/preview-news', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({content, tags: [tag], sample_size: 8}),
    });
    const d = await r.json();
    if (d.error) {
      $('newsList').innerHTML = '<div class="empty-state">' + escHtml(d.error) + '</div>';
    } else if (!d.results || !d.results.length) {
      $('newsList').innerHTML = '<div class="empty-state">未找到匹配的新闻样本</div>';
    } else {
      $('newsList').innerHTML = d.results.map((item, i) =>
        '<div class="news-item">' +
        '<div class="news-title">' + (i + 1) + '. ' + escHtml(item.title) + '</div>' +
        '<div class="news-meta">' +
        '<span class="news-score">匹配度：' + (item.score * 100).toFixed(0) + '%</span>' +
        (item.source ? ' &middot; ' + escHtml(item.source) : '') +
        '</div></div>'
      ).join('');
    }
  } catch(e) {
    $('newsList').innerHTML = '<div class="empty-state">Request failed: ' + escHtml(e.message) + '</div>';
  }
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

loadInterests();
</script>
</body>
</html>"""


def _load_interests():
    if INTERESTS_FILE.exists():
        return INTERESTS_FILE.read_text(encoding="utf-8")
    return ""


def _save_interests(content: str):
    INTERESTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    INTERESTS_FILE.write_text(content, encoding="utf-8")
    logger.info("Interests saved: %d chars", len(content))


def _ai_extract_tags(content: str) -> dict:
    if not AI_API_KEY:
        return {"error": "AI_API_KEY not configured"}

    prompt_template = ""
    if EXTRACT_PROMPT_FILE.exists():
        prompt_template = EXTRACT_PROMPT_FILE.read_text(encoding="utf-8")

    system_prompt = ""
    user_prompt = content
    if "[system]" in prompt_template and "[user]" in prompt_template:
        parts = prompt_template.split("[user]")
        system_prompt = parts[0].replace("[system]", "").strip()
        user_prompt = parts[1].strip() if len(parts) > 1 else content
        user_prompt = user_prompt.replace("{interests_content}", content)

    try:
        import litellm
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        response = litellm.completion(
            model=AI_MODEL,
            messages=messages,
            api_key=AI_API_KEY,
            api_base=AI_API_BASE or None,
            timeout=AI_TIMEOUT,
            max_tokens=AI_MAX_TOKENS,
            temperature=AI_TEMPERATURE,
        )
        raw = response.choices[0].message.content.strip()
        json_str = raw
        if "```json" in raw:
            json_str = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            json_str = raw.split("```")[1].split("```")[0].strip()
        result = json.loads(json_str)
        return {"tags": result.get("tags", [])}
    except json.JSONDecodeError as e:
        logger.error("Bad AI JSON: %s", raw[:300])
        return {"error": f"AI response parse error: {e}"}
    except Exception as e:
        logger.error("AI extract failed: %s", traceback.format_exc())
        return {"error": str(e)}


def _ai_classify_news(content: str, tags: list, sample_size: int = 8) -> dict:
    if not AI_API_KEY:
        return {"error": "AI_API_KEY not configured"}

    recent_news = _load_recent_news(sample_size * 5)
    if not recent_news:
        return {"results": []}

    tags_text = "\n".join(
        f"{i + 1}. {t['tag']}: {t.get('description', '')}"
        for i, t in enumerate(tags)
    )
    classify_prompt = (
        f"用户兴趣标签：\n{tags_text}\n\n"
        f"以下是 {len(recent_news)} 条新闻标题。"
        f"将每条新闻匹配到上面最相关的标签。\n"
        f"评分 0.0-1.0，只返回 score >= 0.5 的结果，最多 {sample_size} 条。\n\n"
        f"新闻列表：\n"
    )
    for i, news in enumerate(recent_news):
        classify_prompt += f"{i + 1}. [{news.get('source', '')}] {news['title']}\n"

    classify_prompt += '\n返回 JSON：{"results": [{"title": "...", "score": 0.9, "source": "...", "tag": "匹配的标签名"}]}'

    try:
        import litellm
        response = litellm.completion(
            model=AI_MODEL,
            messages=[{"role": "user", "content": classify_prompt}],
            api_key=AI_API_KEY,
            api_base=AI_API_BASE or None,
            timeout=AI_TIMEOUT,
            max_tokens=AI_MAX_TOKENS,
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip()
        json_str = raw
        if "```json" in raw:
            json_str = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            json_str = raw.split("```")[1].split("```")[0].strip()
        return json.loads(json_str)
    except Exception as e:
        logger.error("AI classify failed: %s", traceback.format_exc())
        return {"error": str(e)}


def _load_recent_news(limit: int = 40) -> list:
    try:
        db_dir = OUTPUT_DIR / "news"
        if not db_dir.exists():
            return []
        db_files = sorted(db_dir.glob("*.db"), reverse=True)
        if not db_files:
            return []

        import sqlite3
        conn = sqlite3.connect(str(db_files[0]))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT DISTINCT title, platform_id FROM news_items "
            "ORDER BY last_crawl_time DESC LIMIT ?",
            (limit,)
        )
        rows = [{"title": r["title"], "source": r["platform_id"]} for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        logger.error("DB read failed: %s", e)
        return []


# ---- Config helpers ----

def _load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _load_keywords() -> str:
    if KEYWORDS_FILE.exists():
        return KEYWORDS_FILE.read_text(encoding="utf-8")
    return ""


def _save_keywords(content: str):
    KEYWORDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEYWORDS_FILE.write_text(content, encoding="utf-8")


def _get_version() -> str:
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "?"


def _get_system_status() -> dict:
    cfg = _load_config()
    data = {}
    try:
        news_dir = OUTPUT_DIR / "news"
        if news_dir.exists():
            db_files = list(news_dir.glob("*.db"))
            data["available_dates"] = len(db_files)
            if db_files:
                latest = sorted(db_files)[-1]
                data["latest_date"] = latest.stem
            else:
                data["latest_date"] = "-"
        else:
            data["available_dates"] = 0
            data["latest_date"] = "-"
        storage_files = 0
        for subdir in ["news", "rss", "html"]:
            d = OUTPUT_DIR / subdir
            if d.exists():
                storage_files += len(list(d.rglob("*")))
        data["storage_files"] = storage_files
    except Exception as e:
        logger.error("Status gather failed: %s", e)
        data["available_dates"] = 0
        data["latest_date"] = "-"
        data["storage_files"] = 0
    return {
        "config": cfg,
        "data": data,
        "version": _get_version(),
    }


# ---- HTTP Handler ----
class TrendRadarHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(OUTPUT_DIR), **kwargs)

    def log_message(self, fmt, *args):
        logger.info("%s %s", self.address_string(), fmt % args)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Page routes
        if path == "/":
            self._serve_html(home_page())
        elif path == "/dashboard":
            self._serve_html(dashboard(_get_system_status()))
        elif path == "/platforms":
            self._serve_html(platforms_page())
        elif path == "/rss":
            self._serve_html(rss_page())
        elif path in ("/filter", "/keywords"):
            self._serve_html(filter_page())
        elif path == "/notification":
            self._serve_html(notification_page())
        elif path == "/ai":
            self._serve_html(ai_page())
        elif path == "/my_interest":
            self._serve_html(MY_INTEREST_HTML)
        # API routes
        elif path == "/api/status":
            self._json(_get_system_status())
        elif path == "/api/config/platforms":
            cfg = _load_config()
            self._json({"sources": cfg.get("platforms", {}).get("sources", [])})
        elif path == "/api/config/rss":
            cfg = _load_config()
            self._json({"feeds": cfg.get("rss", {}).get("feeds", [])})
        elif path == "/api/keywords":
            self._json({"content": _load_keywords(), "path": str(KEYWORDS_FILE)})
        elif path == "/api/config/notification":
            cfg = _load_config()
            notif = cfg.get("notification", {})
            self._json({"enabled": notif.get("enabled", True), "email": notif.get("channels", {}).get("email", {})})
        elif path == "/api/config/ai":
            cfg = _load_config()
            ai = cfg.get("ai", {})
            self._json({
                "model": ai.get("model", ""),
                "api_key": ai.get("api_key", ""),
                "api_base": ai.get("api_base", ""),
                "timeout": ai.get("timeout", 120),
                "max_tokens": ai.get("max_tokens", 5000),
                "temperature": ai.get("temperature", 1.0),
                "ai_analysis_enabled": cfg.get("ai_analysis", {}).get("enabled", False),
                "ai_translation_enabled": cfg.get("ai_translation", {}).get("enabled", False),
                "filter_method": cfg.get("filter", {}).get("method", "keyword"),
                "article_content_enabled": cfg.get("article_content", {}).get("enabled", False),
            })
        elif path == "/api/interests":
            self._handle_get_interests()
        elif path == "/api/health":
            self._json({"status": "ok"})
        elif path == "/files":
            saved = self.path
            self.path = "/"
            try:
                super().do_GET()
            finally:
                self.path = saved
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        if path == "/api/interests":
            self._handle_save_interests(body)
        elif path == "/api/interests/preview":
            self._handle_preview_tags(body)
        elif path == "/api/interests/preview-news":
            self._handle_preview_news(body)
        elif path == "/api/config/platforms":
            self._handle_save_platforms(body)
        elif path == "/api/config/rss":
            self._handle_save_rss(body)
        elif path == "/api/keywords":
            self._handle_save_keywords(body)
        elif path == "/api/config/notification":
            self._handle_save_notification(body)
        elif path == "/api/config/ai":
            self._handle_save_ai(body)
        else:
            self._json_error(404, "Not Found")

    def _read_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _serve_html(self, html: str):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _json_error(self, status: int, message: str):
        self._json({"error": message}, status=status)

    def _handle_get_interests(self):
        content = _load_interests()
        self._json({"content": content, "path": str(INTERESTS_FILE)})

    def _handle_save_interests(self, body: dict):
        content = body.get("content", "")
        if not content.strip():
            self._json({"success": False, "error": "Content cannot be empty"}, status=400)
            return
        try:
            _save_interests(content)
            self._json({"success": True, "path": str(INTERESTS_FILE)})
        except Exception as e:
            self._json({"success": False, "error": str(e)}, status=500)

    def _handle_preview_tags(self, body: dict):
        content = body.get("content", "")
        if not content.strip():
            self._json({"error": "Content cannot be empty"}, status=400)
            return
        result = _ai_extract_tags(content)
        self._json(result)

    def _handle_preview_news(self, body: dict):
        tags = body.get("tags", [])
        sample_size = body.get("sample_size", 8)
        if not tags:
            self._json({"error": "tags required"}, status=400)
            return
        result = _ai_classify_news(body.get("content", ""), tags, sample_size)
        self._json(result)

    def _handle_save_platforms(self, body: dict):
        sources = body.get("sources")
        if sources is None:
            self._json({"success": False, "error": "sources required"}, status=400)
            return
        try:
            cfg = _load_config()
            cfg.setdefault("platforms", {})["sources"] = sources
            _save_config(cfg)
            self._json({"success": True})
        except Exception as e:
            self._json({"success": False, "error": str(e)}, status=500)

    def _handle_save_rss(self, body: dict):
        feeds = body.get("feeds")
        if feeds is None:
            self._json({"success": False, "error": "feeds required"}, status=400)
            return
        try:
            cfg = _load_config()
            cfg.setdefault("rss", {})["feeds"] = feeds
            _save_config(cfg)
            self._json({"success": True})
        except Exception as e:
            self._json({"success": False, "error": str(e)}, status=500)

    def _handle_save_keywords(self, body: dict):
        content = body.get("content", "")
        if not content.strip():
            self._json({"success": False, "error": "Content cannot be empty"}, status=400)
            return
        try:
            _save_keywords(content)
            self._json({"success": True, "path": str(KEYWORDS_FILE)})
        except Exception as e:
            self._json({"success": False, "error": str(e)}, status=500)

    def _handle_save_notification(self, body: dict):
        try:
            cfg = _load_config()
            notif = cfg.setdefault("notification", {})
            notif["enabled"] = body.get("enabled", True)
            email = body.get("email", {})
            channels = notif.setdefault("channels", {})
            channels["email"] = {
                "from": email.get("from", ""),
                "password": email.get("password", ""),
                "to": email.get("to", ""),
                "smtp_server": email.get("smtp_server", ""),
                "smtp_port": email.get("smtp_port", ""),
            }
            _save_config(cfg)
            self._json({"success": True})
        except Exception as e:
            self._json({"success": False, "error": str(e)}, status=500)

    def _handle_save_ai(self, body: dict):
        try:
            cfg = _load_config()
            ai = cfg.setdefault("ai", {})
            for key in ("model", "api_key", "api_base", "timeout", "max_tokens", "temperature"):
                if key in body:
                    ai[key] = body[key]
            cfg.setdefault("ai_analysis", {})["enabled"] = body.get("ai_analysis_enabled", True)
            cfg.setdefault("ai_translation", {})["enabled"] = body.get("ai_translation_enabled", True)
            cfg.setdefault("filter", {})["method"] = body.get("filter_method", "keyword")
            cfg.setdefault("article_content", {})["enabled"] = body.get("article_content_enabled", False)
            _save_config(cfg)
            self._json({"success": True})
        except Exception as e:
            self._json({"success": False, "error": str(e)}, status=500)


def start_server(port: int = 9999):
    server = ThreadingHTTPServer(("0.0.0.0", port), TrendRadarHandler)
    logger.info("TrendRadar WebServer started on port %d", port)
    logger.info("  Dashboard: http://0.0.0.0:%d/", port)
    logger.info("  Platforms: http://0.0.0.0:%d/platforms", port)
    logger.info("  Interests: http://0.0.0.0:%d/my_interest", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
