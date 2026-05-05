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

logging.basicConfig(level=logging.INFO, format="[WebServer] %(message)s")
logger = logging.getLogger(__name__)

# ---- Paths ----
OUTPUT_DIR = Path(os.environ.get("WEBSERVER_DIR", "/app/output")).resolve()
CONFIG_DIR = Path(os.environ.get("CONFIG_DIR", "/app/config")).resolve()
APP_DIR = Path(os.environ.get("APP_DIR", "/app")).resolve()
INTERESTS_FILE = CONFIG_DIR / "ai_interests.txt"
EXTRACT_PROMPT_FILE = CONFIG_DIR / "ai_filter" / "extract_prompt.txt"
SINGLE_WATCH_CONFIG_FILE = Path(
    os.environ.get("SINGLE_WATCH_CONFIG_FILE", str(OUTPUT_DIR / "single_watch" / "config.json"))
).resolve()

# Ensure the app dir is importable
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# ---- AI Config from env ----
AI_MODEL = os.environ.get("AI_MODEL", "openai/deepseek-v4")
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
<title>My Interest - TrendRadar</title>
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
  <h1>My Interest Config</h1>
  <p class="subtitle">Describe what you care about in natural language. AI extracts tags and classifies news automatically. Changes take effect on the next scheduled run.</p>

  <div class="card">
    <h2>Interest Description</h2>
    <textarea id="interestsInput" placeholder="Describe topics you care about..."></textarea>
    <div class="btn-row">
      <button class="btn btn-primary" id="btnSave" onclick="saveInterests()">Save</button>
      <button class="btn btn-secondary" id="btnPreview" onclick="previewTags()">AI Preview Tags</button>
      <button class="btn btn-outline" id="btnReset" onclick="loadInterests()">Reload</button>
    </div>
    <div id="status" class="status"></div>
  </div>

  <div class="card" id="tagsCard" style="display:none;">
    <h2>AI-Extracted Tags <span style="font-weight:400;font-size:0.8rem;color:var(--text2);">(drag to reorder priority)</span></h2>
    <div class="tag-list" id="tagList"></div>
    <div class="news-sample" id="newsSample" style="display:none;">
      <h2 style="margin-bottom:12px;">News Samples: <span id="newsSampleTitle"></span></h2>
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
    showStatus('Load failed: ' + e.message, 'error');
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
      showStatus('Saved. Takes effect on next run.', 'success');
    } else {
      showStatus('Save failed: ' + (d.error || 'unknown'), 'error');
    }
  } catch(e) {
    showStatus('Request failed: ' + e.message, 'error');
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
    if (!content.trim()) { showStatus('Please enter interest description first', 'error'); return; }
    const r = await fetch('/api/interests/preview', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({content}),
    });
    const d = await r.json();
    if (d.error) {
      showStatus('AI extraction failed: ' + d.error, 'error');
    } else {
      currentTags = d.tags || [];
      renderTags();
      $('tagsCard').style.display = 'block';
      showStatus('AI extracted ' + currentTags.length + ' tags', 'success');
    }
  } catch(e) {
    showStatus('Request failed: ' + e.message, 'error');
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
    '<button onclick="previewNews(' + i + ')">View Samples</button>' +
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
  $('newsList').innerHTML = '<div class="empty-state"><span class="spinner"></span> AI classifying...</div>';
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
      $('newsList').innerHTML = '<div class="empty-state">No matching news samples found</div>';
    } else {
      $('newsList').innerHTML = d.results.map((item, i) =>
        '<div class="news-item">' +
        '<div class="news-title">' + (i + 1) + '. ' + escHtml(item.title) + '</div>' +
        '<div class="news-meta">' +
        '<span class="news-score">Match: ' + (item.score * 100).toFixed(0) + '%</span>' +
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


SINGLE_WATCH_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Single Watch - TrendRadar</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f6f7f9;color:#1f2937;margin:0;padding:24px}
.wrap{max-width:760px;margin:0 auto;background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:24px}
h1{font-size:22px;margin:0 0 6px}.hint{color:#6b7280;margin:0 0 22px;line-height:1.6}
label{display:block;font-weight:600;margin:16px 0 6px}
input,textarea{width:100%;box-sizing:border-box;border:1px solid #d1d5db;border-radius:6px;padding:10px;font-size:15px}
textarea{min-height:86px;resize:vertical}
.row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
button{margin-top:20px;background:#0b57d0;color:#fff;border:0;border-radius:6px;padding:11px 18px;font-weight:700;cursor:pointer}
button:disabled{opacity:.6;cursor:not-allowed}.status{margin-top:14px;padding:10px;border-radius:6px;display:none}
.ok{display:block;background:#ecfdf3;color:#166534}.err{display:block;background:#fef2f2;color:#991b1b}
.small{font-size:13px;color:#6b7280;margin-top:6px}
</style>
</head>
<body>
<div class="wrap">
  <h1>网页关键词监控</h1>
  <p class="hint">填写要监控的网页、关注主题词和收件邮箱。保存后，后台监控会在下一轮检查时自动使用新配置。</p>

  <label for="watchUrl">网页链接</label>
  <input id="watchUrl" placeholder="例如：http://finance.people.com.cn/">

  <label for="keywords">关注主题词</label>
  <textarea id="keywords" placeholder="例如：具身智能, 机器人, 人形机器人"></textarea>
  <div class="small">多个主题词可用逗号、分号或换行分隔。</div>

  <label for="emailTo">收件邮箱</label>
  <input id="emailTo" placeholder="user@example.com">

  <div class="row">
    <div>
      <label for="sourceName">来源名称</label>
      <input id="sourceName" placeholder="例如：人民网经济科技">
    </div>
    <div>
      <label for="interval">检查间隔（秒）</label>
      <input id="interval" type="number" min="30" placeholder="1800">
    </div>
  </div>

  <button id="saveBtn" onclick="saveConfig()">保存配置</button>
  <div id="status" class="status"></div>
</div>

<script>
function $(id){return document.getElementById(id)}
function status(msg, ok){const el=$('status');el.textContent=msg;el.className='status '+(ok?'ok':'err')}
async function loadConfig(){
  const r=await fetch('/api/single-watch/config');
  const d=await r.json();
  $('watchUrl').value=d.watch_url||'';
  $('keywords').value=Array.isArray(d.keywords)?d.keywords.join(', '):(d.keywords||'');
  $('emailTo').value=d.email_to||'';
  $('sourceName').value=d.source_name||'';
  $('interval').value=d.check_interval||1800;
}
async function saveConfig(){
  const btn=$('saveBtn');btn.disabled=true;
  try{
    const payload={
      watch_url:$('watchUrl').value.trim(),
      keywords:$('keywords').value,
      email_to:$('emailTo').value.trim(),
      source_name:$('sourceName').value.trim(),
      check_interval:Number($('interval').value||1800)
    };
    const r=await fetch('/api/single-watch/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const d=await r.json();
    if(!r.ok||!d.success){status(d.error||'保存失败',false)}else{status('已保存。下一轮监控会自动使用新配置。',true)}
  }catch(e){status('请求失败：'+e.message,false)}
  finally{btn.disabled=false}
}
loadConfig().catch(e=>status('加载失败：'+e.message,false));
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
        f"User interest tags:\n{tags_text}\n\n"
        f"Below are {len(recent_news)} news headlines. Match news to tag \"{tags[0]['tag']}\".\n"
        f"Score each match 0.0-1.0. Only return items with score >= 0.5. Max {sample_size} results.\n\n"
        f"News:\n"
    )
    for i, news in enumerate(recent_news):
        classify_prompt += f"{i + 1}. [{news.get('source', '')}] {news['title']}\n"

    classify_prompt += '\nReturn JSON: {"results": [{"title": "...", "score": 0.9, "source": "..."}]}'

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
            "SELECT DISTINCT title, platform_name FROM news_items "
            "ORDER BY last_time DESC LIMIT ?",
            (limit,)
        )
        rows = [{"title": r["title"], "source": r["platform_name"]} for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        logger.error("DB read failed: %s", e)
        return []


# ---- HTTP Handler ----
class TrendRadarHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(OUTPUT_DIR), **kwargs)

    def log_message(self, fmt, *args):
        logger.info("%s %s", self.address_string(), fmt % args)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/my_interest":
            self._serve_html(MY_INTEREST_HTML)
        elif path == "/single_watch":
            self._serve_html(SINGLE_WATCH_HTML)
        elif path == "/api/interests":
            self._handle_get_interests()
        elif path == "/api/single-watch/config":
            self._handle_get_single_watch_config()
        elif path == "/api/health":
            self._json({"status": "ok"})
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
        elif path == "/api/single-watch/config":
            self._handle_save_single_watch_config(body)
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

    def _handle_get_single_watch_config(self):
        data = {}
        if SINGLE_WATCH_CONFIG_FILE.exists():
            try:
                data = json.loads(SINGLE_WATCH_CONFIG_FILE.read_text(encoding="utf-8"))
            except Exception as e:
                self._json({"error": f"Config read failed: {e}"}, status=500)
                return
        data.setdefault("watch_url", os.environ.get("WATCH_URL", ""))
        data.setdefault("keywords", os.environ.get("WATCH_KEYWORDS", ""))
        data.setdefault("email_to", os.environ.get("EMAIL_TO", ""))
        data.setdefault("source_name", os.environ.get("WATCH_SOURCE_NAME", ""))
        data.setdefault("check_interval", int(os.environ.get("CHECK_INTERVAL", "1800") or "1800"))
        data["path"] = str(SINGLE_WATCH_CONFIG_FILE)
        self._json(data)

    def _handle_save_single_watch_config(self, body: dict):
        watch_url = str(body.get("watch_url", "")).strip()
        keywords_raw = body.get("keywords", "")
        email_to = str(body.get("email_to", "")).strip()
        source_name = str(body.get("source_name", "")).strip() or "Watch Source"

        if not watch_url.startswith(("http://", "https://")):
            self._json({"success": False, "error": "网页链接必须以 http:// 或 https:// 开头"}, status=400)
            return
        if "@" not in email_to or "." not in email_to.split("@")[-1]:
            self._json({"success": False, "error": "请填写有效的收件邮箱"}, status=400)
            return

        if isinstance(keywords_raw, list):
            keywords = [str(item).strip() for item in keywords_raw if str(item).strip()]
        else:
            import re
            keywords = [item.strip() for item in re.split(r"[,;，；\n]+", str(keywords_raw)) if item.strip()]
        if not keywords:
            self._json({"success": False, "error": "请至少填写一个关注主题词"}, status=400)
            return

        try:
            check_interval = int(body.get("check_interval", 1800))
            check_interval = max(30, check_interval)
        except (TypeError, ValueError):
            check_interval = 1800

        payload = {
            "watch_url": watch_url,
            "keywords": keywords,
            "email_to": email_to,
            "source_name": source_name,
            "check_interval": check_interval,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }

        try:
            SINGLE_WATCH_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            SINGLE_WATCH_CONFIG_FILE.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self._json({"success": True, "path": str(SINGLE_WATCH_CONFIG_FILE)})
        except Exception as e:
            self._json({"success": False, "error": str(e)}, status=500)


def start_server(port: int = 9999):
    server = ThreadingHTTPServer(("0.0.0.0", port), TrendRadarHandler)
    logger.info("TrendRadar WebServer started on port %d", port)
    logger.info("  Static: http://0.0.0.0:%d/", port)
    logger.info("  Interests: http://0.0.0.0:%d/my_interest", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
