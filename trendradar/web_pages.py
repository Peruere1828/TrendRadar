"""
HTML page templates for TrendRadar Web Management Dashboard.
Each function returns a complete HTML page string with light theme
CSS and top navigation bar. Imported by trendradar.webserver.
"""

SHARED_CSS = """
:root {
  --bg: #f5f6fa; --card: #fff; --card2: #eef0f6;
  --text: #2d3436; --text2: #636e72; --accent: #e94560;
  --green: #00b894; --blue: #0984e3; --yellow: #fdcb6e;
  --border: #dfe6e9; --radius: 10px;
  --shadow: 0 1px 3px rgba(0,0,0,0.08);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg); color: var(--text); min-height: 100vh;
}
nav {
  background: #fff; border-bottom: 1px solid var(--border);
  padding: 0 20px; display: flex; align-items: center; gap: 4px;
  position: sticky; top: 0; z-index: 100; overflow-x: auto;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
nav .brand { font-weight: 700; font-size: 1.1rem; color: var(--accent); margin-right: 20px; white-space: nowrap; }
nav a {
  color: var(--text2); text-decoration: none; padding: 14px 12px;
  font-size: 0.88rem; border-bottom: 2px solid transparent; white-space: nowrap;
  transition: all 0.15s;
}
nav a:hover, nav a.active { color: var(--accent); border-bottom-color: var(--accent); }
.container { max-width: 1100px; margin: 0 auto; padding: 24px 20px; }
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 1.4rem; margin-bottom: 6px; }
.page-header p { color: var(--text2); font-size: 0.9rem; }
.card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px; margin-bottom: 20px;
  box-shadow: var(--shadow);
}
.card h2 { font-size: 1.05rem; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
.card h3 { font-size: 0.95rem; margin-bottom: 10px; color: var(--text2); }
.stat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
.stat-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 8px; padding: 20px;
  box-shadow: var(--shadow); cursor: default;
}
.stat-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.12); }
.stat-card .stat-value { font-size: 1.4rem; font-weight: 700; color: var(--text); }
.stat-card .stat-label { font-size: 0.82rem; color: var(--text2); margin-top: 4px; }
.btn-row { display: flex; gap: 10px; margin-top: 14px; flex-wrap: wrap; }
.btn {
  padding: 9px 20px; border: none; border-radius: 8px;
  font-size: 0.9rem; cursor: pointer; font-weight: 600;
  transition: all 0.15s; display: inline-flex; align-items: center; gap: 6px;
}
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover { filter: brightness(1.1); }
.btn-secondary { background: var(--blue); color: #fff; }
.btn-secondary:hover { filter: brightness(1.1); }
.btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text2); }
.btn-outline:hover { background: var(--card2); color: var(--text); }
.btn-danger { background: #d63031; color: #fff; }
.btn-danger:hover { filter: brightness(1.1); }
.btn-sm { padding: 5px 12px; font-size: 0.8rem; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
label { display: block; font-size: 0.88rem; font-weight: 600; margin-bottom: 6px; color: var(--text2); }
input, textarea, select {
  width: 100%; background: #fff; color: var(--text);
  border: 1px solid var(--border); border-radius: 6px;
  padding: 10px 12px; font-size: 0.9rem; font-family: inherit;
}
input:focus, textarea:focus, select:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px rgba(233,69,96,0.1); }
textarea { resize: vertical; min-height: 100px; line-height: 1.5; }
.form-group { margin-bottom: 16px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 10px 14px; text-align: left; font-size: 0.88rem; }
th { color: var(--text2); font-weight: 600; border-bottom: 2px solid var(--border); background: var(--card2); }
td { border-bottom: 1px solid var(--border); }
tr:hover td { background: var(--card2); }
.status {
  margin-top: 12px; padding: 10px 14px; border-radius: 6px;
  font-size: 0.85rem; display: none;
}
.status.success { background: rgba(0,184,148,0.1); color: #00896b; display: block; }
.status.error { background: rgba(233,69,96,0.1); color: #c0392b; display: block; }
.status.info { background: rgba(9,132,227,0.1); color: #0666b0; display: block; }
.spinner {
  display: inline-block; width: 16px; height: 16px;
  border: 2px solid rgba(0,0,0,0.15);
  border-top-color: var(--blue); border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.toggle {
  position: relative; display: inline-block; width: 44px; height: 24px;
}
.toggle input { opacity: 0; width: 0; height: 0; }
.toggle .slider {
  position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
  background: #ccc; border-radius: 24px; transition: 0.2s;
}
.toggle .slider::before {
  content: ""; position: absolute; height: 18px; width: 18px;
  left: 3px; bottom: 3px; background: #fff; border-radius: 50%; transition: 0.2s;
}
.toggle input:checked + .slider { background: var(--green); }
.toggle input:checked + .slider::before { transform: translateX(20px); }
.badge {
  display: inline-block; padding: 3px 8px; border-radius: 4px;
  font-size: 0.75rem; font-weight: 600;
}
.badge-green { background: rgba(0,184,148,0.12); color: #00896b; }
.badge-red { background: rgba(214,48,49,0.1); color: #c0392b; }
.badge-blue { background: rgba(9,132,227,0.1); color: #0666b0; }
.empty-state { text-align: center; padding: 40px; color: var(--text2); }
.flex-between { display: flex; justify-content: space-between; align-items: center; }
.inline-input {
  background: transparent; border: 1px solid transparent; color: var(--text);
  padding: 4px 6px; border-radius: 4px; font-size: 0.88rem; width: auto;
}
.inline-input:hover { border-color: var(--border); }
.inline-input:focus { border-color: var(--accent); background: #fff; }
.drag-handle { color: var(--text2); cursor: grab; user-select: none; font-size: 1.1rem; }
.modal-overlay {
  display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4); z-index: 200; align-items: center; justify-content: center;
}
.modal-overlay.open { display: flex; }
.modal {
  background: #fff; border: 1px solid var(--border);
  border-radius: var(--radius); padding: 24px; width: 90%; max-width: 550px;
  max-height: 80vh; overflow-y: auto; box-shadow: 0 4px 24px rgba(0,0,0,0.15);
}
.modal h2 { margin-bottom: 16px; }
.stat-card a { text-decoration: none; color: inherit; }
"""

NAV_HTML = """
<nav>
  <span class="brand">&#9873; TrendRadar</span>
  <a href="/" class="nav-home">新闻首页</a>
  <a href="/dashboard" class="nav-dashboard">仪表盘</a>
  <a href="/platforms" class="nav-platforms">平台管理</a>
  <a href="/rss" class="nav-rss">RSS 订阅</a>
  <a href="/filter" class="nav-filter">内容筛选</a>
  <a href="/notification" class="nav-notification">通知设置</a>
  <a href="/ai" class="nav-ai">AI 设置</a>
</nav>
"""


def _layout(title: str, content: str, active_nav: str = "") -> str:
    nav = NAV_HTML.replace(f'nav-{active_nav}"', f'nav-{active_nav} active"') if active_nav else NAV_HTML
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - TrendRadar</title>
<style>{SHARED_CSS}</style>
</head>
<body>
{nav}
<div class="container">
{content}
</div>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════
# Homepage
# ═══════════════════════════════════════════════════════════════

def home_page() -> str:
    content = """<div class="page-header">
  <h1>&#9873; TrendRadar 热点新闻分析</h1>
  <p>一站式新闻聚合、AI 分析与推送系统</p>
</div>

<div class="stat-grid">
  <a href="/html/latest/current.html" style="text-decoration:none">
    <div class="stat-card" style="cursor:pointer;transition:all 0.2s">
      <div class="stat-value" style="font-size:1.2rem">&#128240; 最新热榜</div>
      <div class="stat-label">查看当前热点新闻报告</div>
    </div>
  </a>
  <a href="/html/latest/daily.html" style="text-decoration:none">
    <div class="stat-card" style="cursor:pointer;transition:all 0.2s">
      <div class="stat-value" style="font-size:1.2rem">&#128197; 当日汇总</div>
      <div class="stat-label">查看当日全部新闻汇总</div>
    </div>
  </a>
  <a href="/dashboard" style="text-decoration:none">
    <div class="stat-card" style="cursor:pointer;transition:all 0.2s">
      <div class="stat-value" style="font-size:1.2rem">&#128202; 系统仪表盘</div>
      <div class="stat-label">查看系统运行状态</div>
    </div>
  </a>
  <a href="/my_interest" style="text-decoration:none">
    <div class="stat-card" style="cursor:pointer;transition:all 0.2s">
      <div class="stat-value" style="font-size:1.2rem">&#128269; 兴趣管理</div>
      <div class="stat-label">管理 AI 兴趣标签</div>
    </div>
  </a>
</div>

<div class="card">
  <h2>管理后台</h2>
  <div class="btn-row">
    <button class="btn btn-secondary" onclick="location.href='/dashboard'">&#128202; 仪表盘</button>
    <button class="btn btn-secondary" onclick="location.href='/platforms'">&#127760; 平台管理</button>
    <button class="btn btn-secondary" onclick="location.href='/rss'">&#128240; RSS 订阅</button>
    <button class="btn btn-secondary" onclick="location.href='/filter'">&#128270; 内容筛选</button>
    <button class="btn btn-outline" onclick="location.href='/notification'">&#9993; 通知设置</button>
    <button class="btn btn-outline" onclick="location.href='/ai'">&#129302; AI 设置</button>
    <button class="btn btn-outline" onclick="location.href='/filter'">&#128270; 内容筛选</button>
  </div>
</div>

<div class="card">
  <h2>快速入口</h2>
  <table>
    <tr><td style="width:200px">&#128240; 最新热榜</td><td><a href="/html/latest/current.html" style="color:var(--blue)">/html/latest/current.html</a></td></tr>
    <tr><td>&#128197; 当日汇总</td><td><a href="/html/latest/daily.html" style="color:var(--blue)">/html/latest/daily.html</a></td></tr>
    <tr><td>&#128193; 浏览数据文件</td><td><a href="/files" style="color:var(--blue)">/files</a></td></tr>
  </table>
</div>"""
    return _layout("首页", content, "home")


# ═══════════════════════════════════════════════════════════════
# Dashboard
# ═══════════════════════════════════════════════════════════════

def dashboard(status: dict) -> str:
    cfg = status.get("config", {})
    data = status.get("data", {})
    version = status.get("version", "?")

    platforms = cfg.get("platforms", {}).get("sources", [])
    platforms_count = len(platforms)
    platforms_enabled = sum(1 for s in platforms if s.get("enabled", True))
    feeds = cfg.get("rss", {}).get("feeds", [])
    rss_count = len(feeds)
    rss_enabled = sum(1 for f in feeds if f.get("enabled", True))
    filter_method = cfg.get("filter", {}).get("method", "keyword")
    filter_label = "AI 智能筛选" if filter_method == "ai" else "关键词筛选"
    schedule_preset = cfg.get("schedule", {}).get("preset", "morning_evening")
    preset_labels = {
        "always_on": "全天监控", "morning_evening": "早晚汇总",
        "office_hours": "办公时间", "night_owl": "夜猫子模式", "custom": "自定义",
    }
    schedule_label = preset_labels.get(schedule_preset, schedule_preset)
    ai_enabled = cfg.get("ai_analysis", {}).get("enabled", False)
    translation_enabled = cfg.get("ai_translation", {}).get("enabled", False)
    notif = cfg.get("notification", {})
    notif_channels = notif.get("channels", {})
    active_channels = []
    for ch_name, ch_cfg in notif_channels.items():
        if ch_name == "email":
            if ch_cfg.get("from") and ch_cfg.get("to"):
                active_channels.append("邮件")
        elif ch_cfg.get("webhook_url") or ch_cfg.get("bot_token") or ch_cfg.get("url"):
            active_channels.append(ch_name)
    notif_status = "已启用" if active_channels else "未配置"
    available_dates = data.get("available_dates", 0)
    latest_date = data.get("latest_date", "-")
    storage_count = data.get("storage_files", 0)

    content = f"""<div class="page-header">
  <h1>系统仪表盘</h1>
  <p>TrendRadar v{version} — 系统运行状态概览</p>
</div>

<div class="stat-grid">
  <div class="stat-card">
    <div class="stat-value">{platforms_enabled}/{platforms_count}</div>
    <div class="stat-label">热榜平台已启用</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{rss_enabled}/{rss_count}</div>
    <div class="stat-label">RSS 源已启用</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{available_dates}</div>
    <div class="stat-label">历史数据天数</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{storage_count}</div>
    <div class="stat-label">存储文件数</div>
  </div>
</div>

<div class="card">
  <h2>配置概要</h2>
  <table>
    <tr><td style="width:200px;color:var(--text2)">筛选方式</td><td><span class="badge badge-blue">{filter_label}</span></td></tr>
    <tr><td style="color:var(--text2)">调度预设</td><td>{schedule_label}</td></tr>
    <tr><td style="color:var(--text2)">通知状态</td><td><span class="badge {'badge-green' if active_channels else 'badge-red'}">{notif_status}</span> {"(" + ", ".join(active_channels) + ")" if active_channels else ""}</td></tr>
    <tr><td style="color:var(--text2)">AI 分析</td><td><span class="badge {'badge-green' if ai_enabled else 'badge-red'}">{'已启用' if ai_enabled else '已禁用'}</span></td></tr>
    <tr><td style="color:var(--text2)">AI 翻译</td><td><span class="badge {'badge-green' if translation_enabled else 'badge-red'}">{'已启用' if translation_enabled else '已禁用'}</span></td></tr>
    <tr><td style="color:var(--text2)">最新数据日期</td><td>{latest_date}</td></tr>
  </table>
</div>

<div class="card">
  <h2>快捷操作</h2>
  <div class="btn-row">
    <button class="btn btn-secondary" onclick="location.href='/platforms'">管理平台</button>
    <button class="btn btn-secondary" onclick="location.href='/rss'">管理 RSS</button>
    <button class="btn btn-secondary" onclick="location.href='/keywords'">编辑关键词</button>
    <button class="btn btn-outline" onclick="location.href='/notification'">通知设置</button>
  </div>
</div>"""
    return _layout("仪表盘", content, "dashboard")


# ═══════════════════════════════════════════════════════════════
# Platforms
# ═══════════════════════════════════════════════════════════════

PLATFORMS_SCRIPT = r"""
let platforms = [];
let hasChanges = false;

async function loadPlatforms() {
  try {
    const r = await fetch('/api/config/platforms');
    const d = await r.json();
    platforms = d.sources || [];
    renderTable();
  } catch(e) { showStatus('加载失败: ' + e.message, 'error'); }
}

function renderTable() {
  const tbody = document.getElementById('platformTable');
  tbody.innerHTML = platforms.map((p, i) =>
    `<tr>
      <td><span class="drag-handle">&#9776;</span></td>
      <td><code style="color:var(--blue)">${escHtml(p.id)}</code></td>
      <td><input class="inline-input" value="${escHtml(p.name)}" data-idx="${i}" data-field="name" style="width:180px"></td>
      <td>
        <label class="toggle">
          <input type="checkbox" ${p.enabled !== false ? 'checked' : ''} data-idx="${i}" onchange="togglePlatform(${i}, this.checked)">
          <span class="slider"></span>
        </label>
      </td>
      <td><span class="badge ${p.enabled !== false ? 'badge-green' : 'badge-red'}">${p.enabled !== false ? '已启用' : '已禁用'}</span></td>
    </tr>`
  ).join('');

  tbody.querySelectorAll('.inline-input').forEach(inp => {
    inp.addEventListener('change', () => {
      const idx = parseInt(inp.dataset.idx);
      platforms[idx].name = inp.value;
      hasChanges = true;
    });
  });
}

function togglePlatform(idx, enabled) {
  platforms[idx].enabled = enabled;
  hasChanges = true;
  renderTable();
}

async function savePlatforms() {
  const btn = document.getElementById('btnSave');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> 保存中...';
  try {
    const r = await fetch('/api/config/platforms', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({sources: platforms}),
    });
    const d = await r.json();
    if (d.success) { showStatus('保存成功，下次抓取生效', 'success'); hasChanges = false; }
    else { showStatus('保存失败: ' + (d.error || '未知错误'), 'error'); }
  } catch(e) { showStatus('请求失败: ' + e.message, 'error'); }
  finally { btn.disabled = false; btn.innerHTML = '保存更改'; }
}

function addPlatform() {
  const id = document.getElementById('newPlatformId').value.trim();
  const name = document.getElementById('newPlatformName').value.trim();
  if (!id || !name) { showStatus('平台 ID 和名称不能为空', 'error'); return; }
  if (platforms.find(p => p.id === id)) { showStatus('平台 ID 已存在', 'error'); return; }
  platforms.push({id, name, enabled: true});
  hasChanges = true; renderTable();
  document.getElementById('newPlatformId').value = '';
  document.getElementById('newPlatformName').value = '';
}

function showStatus(msg, type) {
  const el = document.getElementById('status');
  el.textContent = msg; el.className = 'status ' + type;
  setTimeout(() => { if (el.textContent === msg) el.className = 'status'; }, 5000);
}
function escHtml(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
loadPlatforms();
"""


def platforms_page() -> str:
    content = f"""<div class="page-header">
  <h1>热榜平台管理</h1>
  <p>启用、禁用或重命名热榜数据源。平台 ID 对应 NewsNow API 标识符。</p>
</div>

<div class="card">
  <div class="flex-between" style="margin-bottom:14px">
    <h2 style="margin-bottom:0">已配置平台</h2>
    <button class="btn btn-primary btn-sm" onclick="savePlatforms()" id="btnSave">保存更改</button>
  </div>

  <table>
    <thead><tr><th style="width:40px"></th><th>平台 ID</th><th>显示名称</th><th style="width:80px">状态</th><th style="width:90px"></th></tr></thead>
    <tbody id="platformTable"></tbody>
  </table>
  <div id="status" class="status"></div>

  <div style="margin-top:20px; padding-top:16px; border-top:1px solid var(--border)">
    <h3>添加新平台</h3>
    <div class="form-row" style="margin-top:12px">
      <div class="form-group"><label>平台 ID</label><input id="newPlatformId" placeholder="例如: myplatform"></div>
      <div class="form-group"><label>显示名称</label><input id="newPlatformName" placeholder="例如: 我的平台"></div>
    </div>
    <button class="btn btn-outline btn-sm" onclick="addPlatform()">+ 添加平台</button>
  </div>
</div>

<script>{PLATFORMS_SCRIPT}</script>"""
    return _layout("平台管理", content, "platforms")


# ═══════════════════════════════════════════════════════════════
# RSS Feeds
# ═══════════════════════════════════════════════════════════════

RSS_SCRIPT = r"""
let feeds = []; let hasChanges = false; let editingIdx = -1;

async function loadFeeds() {
  try {
    const r = await fetch('/api/config/rss');
    const d = await r.json();
    feeds = d.feeds || [];
    renderTable();
  } catch(e) { showStatus('加载失败: ' + e.message, 'error'); }
}

function renderTable() {
  const tbody = document.getElementById('rssTable');
  if (!feeds.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-state">暂无 RSS 订阅源，请在下方添加</td></tr>';
    return;
  }
  tbody.innerHTML = feeds.map((f, i) =>
    `<tr>
      <td><code style="color:var(--blue)">${escHtml(f.id)}</code></td>
      <td><input class="inline-input" value="${escHtml(f.name)}" data-idx="${i}" data-field="name" style="width:160px"></td>
      <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escHtml(f.url || f.sitemap_url || '')}">${escHtml(f.url || f.sitemap_url || '-')}</td>
      <td>
        <label class="toggle">
          <input type="checkbox" ${f.enabled !== false ? 'checked' : ''} data-idx="${i}" onchange="toggleFeed(${i}, this.checked)">
          <span class="slider"></span>
        </label>
      </td>
      <td><span class="badge ${f.enabled !== false ? 'badge-green' : 'badge-red'}">${f.enabled !== false ? '已启用' : '已禁用'}</span></td>
      <td>
        <button class="btn btn-outline btn-sm" onclick="editFeed(${i})">编辑</button>
        <button class="btn btn-danger btn-sm" onclick="deleteFeed(${i})">删除</button>
      </td>
    </tr>`
  ).join('');
  tbody.querySelectorAll('.inline-input').forEach(inp => {
    inp.addEventListener('change', () => {
      const idx = parseInt(inp.dataset.idx);
      feeds[idx].name = inp.value; hasChanges = true;
    });
  });
}

function toggleFeed(idx, enabled) { feeds[idx].enabled = enabled; hasChanges = true; renderTable(); }

function editFeed(idx) {
  editingIdx = idx; const f = feeds[idx];
  document.getElementById('editId').value = f.id;
  document.getElementById('editName').value = f.name;
  document.getElementById('editUrl').value = f.url || f.sitemap_url || '';
  document.getElementById('editMaxAge').value = f.max_age_days ?? '';
  document.getElementById('editSitemapUrl').value = f.sitemap_url || '';
  document.getElementById('feedModal').classList.add('open');
}

function deleteFeed(idx) {
  if (!confirm('确定删除订阅源 "' + feeds[idx].name + '"？')) return;
  feeds.splice(idx, 1); hasChanges = true; renderTable();
}

function saveFeed() {
  const feed = { id: document.getElementById('editId').value.trim(), name: document.getElementById('editName').value.trim() };
  const url = document.getElementById('editUrl').value.trim();
  const sitemap = document.getElementById('editSitemapUrl').value.trim();
  const maxAge = document.getElementById('editMaxAge').value.trim();
  if (!feed.id || !feed.name) { showStatus('ID 和名称不能为空', 'error'); return; }
  if (sitemap) feed.sitemap_url = sitemap;
  else if (url) feed.url = url;
  if (maxAge) feed.max_age_days = parseInt(maxAge);
  if (editingIdx >= 0) { feeds[editingIdx] = { ...feeds[editingIdx], ...feed }; }
  else {
    if (feeds.find(f => f.id === feed.id)) { showStatus('订阅源 ID 已存在', 'error'); return; }
    feed.enabled = true; feeds.push(feed);
  }
  hasChanges = true; editingIdx = -1; closeModal(); renderTable();
}

function newFeed() {
  editingIdx = -1;
  document.getElementById('editId').value = '';
  document.getElementById('editName').value = '';
  document.getElementById('editUrl').value = '';
  document.getElementById('editMaxAge').value = '';
  document.getElementById('editSitemapUrl').value = '';
  document.getElementById('feedModal').classList.add('open');
}
function closeModal() { document.getElementById('feedModal').classList.remove('open'); }

async function saveFeeds() {
  const btn = document.getElementById('btnSave'); btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> 保存中...';
  try {
    const r = await fetch('/api/config/rss', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({feeds}),
    });
    const d = await r.json();
    if (d.success) { showStatus('保存成功', 'success'); hasChanges = false; }
    else { showStatus('保存失败: ' + (d.error || '未知错误'), 'error'); }
  } catch(e) { showStatus('请求失败: ' + e.message, 'error'); }
  finally { btn.disabled = false; btn.innerHTML = '保存更改'; }
}

function showStatus(msg, type) {
  const el = document.getElementById('status');
  el.textContent = msg; el.className = 'status ' + type;
  setTimeout(() => { if (el.textContent === msg) el.className = 'status'; }, 5000);
}
function escHtml(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
loadFeeds();
"""


def rss_page() -> str:
    content = f"""<div class="page-header">
  <h1>RSS 订阅管理</h1>
  <p>管理 RSS/Atom/JSON Feed 订阅源。RSS 数据会与热榜数据一起抓取。</p>
</div>

<div class="card">
  <div class="flex-between" style="margin-bottom:14px">
    <h2 style="margin-bottom:0">已订阅源</h2>
    <div style="display:flex;gap:8px">
      <button class="btn btn-outline btn-sm" onclick="newFeed()">+ 添加订阅</button>
      <button class="btn btn-primary btn-sm" onclick="saveFeeds()" id="btnSave">保存更改</button>
    </div>
  </div>

  <table>
    <thead><tr><th>Feed ID</th><th>名称</th><th>URL</th><th style="width:80px">状态</th><th style="width:90px"></th><th style="width:100px">操作</th></tr></thead>
    <tbody id="rssTable"></tbody>
  </table>
  <div id="status" class="status"></div>
</div>

<div class="modal-overlay" id="feedModal">
  <div class="modal">
    <h2>编辑 RSS 订阅</h2>
    <div class="form-group"><label>Feed ID</label><input id="editId" placeholder="例如: my-feed"></div>
    <div class="form-group"><label>显示名称</label><input id="editName" placeholder="例如: 我的订阅"></div>
    <div class="form-group"><label>RSS/Atom URL</label><input id="editUrl" placeholder="https://example.com/feed.xml"></div>
    <div class="form-group"><label>Sitemap URL（备选）</label><input id="editSitemapUrl" placeholder="https://example.com/sitemap.xml"></div>
    <div class="form-group"><label>最大文章天数（可选）</label><input id="editMaxAge" type="number" placeholder="留空使用全局默认值"></div>
    <div class="btn-row">
      <button class="btn btn-primary" onclick="saveFeed()">保存</button>
      <button class="btn btn-outline" onclick="closeModal()">取消</button>
    </div>
  </div>
</div>

<script>{RSS_SCRIPT}</script>"""
    return _layout("RSS 订阅", content, "rss")


# ═══════════════════════════════════════════════════════════════
# Unified Content Filter Page
# ═══════════════════════════════════════════════════════════════

FILTER_SCRIPT = r"""
let currentMethod = 'ai';

async function loadFilter() {
  try {
    const [aiResp, kwResp, intResp] = await Promise.all([
      fetch('/api/config/ai'),
      fetch('/api/keywords'),
      fetch('/api/interests'),
    ]);
    const ai = await aiResp.json();
    const kw = await kwResp.json();
    const int = await intResp.json();

    currentMethod = ai.filter_method || 'ai';
    document.getElementById('methodToggle').value = currentMethod;
    document.getElementById('intContent').value = int.content || '';
    document.getElementById('kwContent').value = kw.content || '';
    switchPanel(currentMethod);
  } catch(e) { showStatus('加载失败: ' + e.message, 'error'); }
}

function switchPanel(method) {
  currentMethod = method;
  document.getElementById('panel-ai').style.display = method === 'ai' ? 'block' : 'none';
  document.getElementById('panel-kw').style.display = method === 'keyword' ? 'block' : 'none';
  document.getElementById('methodToggle').value = method;
}

async function saveFilter() {
  const btn = document.getElementById('btnSave');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> 保存中...';
  try {
    // Save filter method
    await fetch('/api/config/ai', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({filter_method: currentMethod}),
    });

    // Save both files' content
    const intContent = document.getElementById('intContent').value;
    const kwContent = document.getElementById('kwContent').value;
    await Promise.all([
      fetch('/api/interests', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({content: intContent}),
      }),
      fetch('/api/keywords', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({content: kwContent}),
      }),
    ]);
    showStatus('保存成功，下次抓取生效', 'success');
  } catch(e) { showStatus('保存失败: ' + e.message, 'error'); }
  finally { btn.disabled = false; btn.innerHTML = '保存设置'; }
}

function showStatus(msg, type) {
  const el = document.getElementById('status');
  el.textContent = msg; el.className = 'status ' + type;
  setTimeout(() => { if (el.textContent === msg) el.className = 'status'; }, 5000);
}
loadFilter();
"""


def filter_page() -> str:
    content = f"""<div class="page-header">
  <h1>内容筛选</h1>
  <p>选择筛选方式并编辑对应的配置文件。两种方式互斥，同一时间只有一种生效。</p>
</div>

<div class="card">
  <div class="flex-between" style="margin-bottom:14px">
    <h2 style="margin-bottom:0">筛选方式</h2>
    <button class="btn btn-primary btn-sm" onclick="saveFilter()" id="btnSave">保存设置</button>
  </div>

  <div class="form-group" style="max-width:400px">
    <label>筛选方式选择</label>
    <select id="methodToggle" onchange="switchPanel(this.value)" style="font-size:1rem;padding:12px">
      <option value="ai">AI 智能筛选 — 用自然语言描述兴趣，AI 自动提取标签并分类新闻</option>
      <option value="keyword">关键词筛选 — 用关键词/正则表达式精确匹配新闻标题</option>
    </select>
  </div>

  <div style="margin-top:14px;padding:12px;background:var(--card2);border-radius:8px;font-size:0.85rem;color:var(--text2)">
    <strong id="methodHint">AI 模式下，系统会用 AI 从你的描述中提取标签，再将新闻按标签分类推送。</strong>
  </div>
  <div id="status" class="status"></div>
</div>

<!-- AI Panel -->
<div class="card" id="panel-ai">
  <h2>兴趣描述（AI 模式）</h2>
  <p style="font-size:0.85rem;color:var(--text2);margin-bottom:12px">
    用自然语言描述你关注的内容方向。从上到下优先级递减，越靠前越重要。
    AI 会从中提取标签并在抓取新闻时自动分类。
  </p>
  <textarea id="intContent" style="min-height:300px;font-family:'SF Mono',Monaco,monospace;font-size:0.85rem;"></textarea>
  <div class="btn-row">
    <button class="btn btn-outline btn-sm" onclick="location.href='/my_interest'">打开标签预览工具</button>
  </div>
</div>

<!-- Keyword Panel -->
<div class="card" id="panel-kw" style="display:none">
  <h2>关键词配置（关键词模式）</h2>
  <p style="font-size:0.85rem;color:var(--text2);margin-bottom:12px">
    定义关键词组用于直接匹配新闻标题。支持正则表达式、分组别名、必须词(+)、排除词(!)、数量限制(@N)。
  </p>
  <textarea id="kwContent" style="min-height:400px;font-family:'SF Mono',Monaco,monospace;font-size:0.85rem;"></textarea>
</div>

<div class="card">
  <h2>语法速查表（关键词模式）</h2>
  <table>
    <tr><td style="width:120px"><code>关键词</code></td><td>普通关键词匹配</td></tr>
    <tr><td><code>/正则/</code></td><td>正则表达式匹配（不区分大小写）</td></tr>
    <tr><td><code>词 => 别名</code></td><td>关键词显示别名</td></tr>
    <tr><td><code>[组名]</code></td><td>分组别名（放在组的第一行）</td></tr>
    <tr><td><code>[GLOBAL_FILTER]</code></td><td>全局过滤区（排除不想看的内容）</td></tr>
    <tr><td><code>+关键词</code></td><td>必须包含关键词（AND 逻辑）</td></tr>
    <tr><td><code>!关键词</code></td><td>排除关键词（NOT 逻辑）</td></tr>
    <tr><td><code>@N</code></td><td>该组最多显示 N 条</td></tr>
  </table>
</div>

<script>
{FILTER_SCRIPT}
document.getElementById('methodToggle').addEventListener('change', function() {{
  const method = this.value;
  switchPanel(method);
  const hint = document.getElementById('methodHint');
  if (method === 'ai') {{
    hint.textContent = 'AI 模式下，系统会用 AI 从你的描述中提取标签，再将新闻按标签分类推送。';
  }} else {{
    hint.textContent = '关键词模式下，系统直接匹配新闻标题中的关键词，速度快且精确。';
  }}
}});
</script>"""
    return _layout("内容筛选", content, "filter")


# ═══════════════════════════════════════════════════════════════
# Notification
# ═══════════════════════════════════════════════════════════════

NOTIFICATION_SCRIPT = r"""
async function loadConfig() {
  try {
    const r = await fetch('/api/config/notification'); const d = await r.json();
    const email = d.email || {};
    document.getElementById('emailFrom').value = email.from || '';
    document.getElementById('emailPassword').value = email.password || '';
    document.getElementById('emailTo').value = email.to || '';
    document.getElementById('emailSmtpServer').value = email.smtp_server || '';
    document.getElementById('emailSmtpPort').value = email.smtp_port || '';
    document.getElementById('notifEnabled').checked = d.enabled !== false;
  } catch(e) { showStatus('加载失败: ' + e.message, 'error'); }
}
async function saveConfig() {
  const btn = document.getElementById('btnSave'); btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> 保存中...';
  try {
    const data = {
      enabled: document.getElementById('notifEnabled').checked,
      email: {
        from: document.getElementById('emailFrom').value.trim(),
        password: document.getElementById('emailPassword').value.trim(),
        to: document.getElementById('emailTo').value.trim(),
        smtp_server: document.getElementById('emailSmtpServer').value.trim(),
        smtp_port: document.getElementById('emailSmtpPort').value.trim(),
      }
    };
    const r = await fetch('/api/config/notification', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data),
    });
    const d = await r.json();
    if (d.success) showStatus('通知配置已保存', 'success');
    else showStatus('保存失败: ' + (d.error || '未知错误'), 'error');
  } catch(e) { showStatus('请求失败: ' + e.message, 'error'); }
  finally { btn.disabled = false; btn.innerHTML = '保存设置'; }
}
function showStatus(msg, type) {
  const el = document.getElementById('status');
  el.textContent = msg; el.className = 'status ' + type;
  setTimeout(() => { if (el.textContent === msg) el.className = 'status'; }, 5000);
}
loadConfig();
"""


def notification_page() -> str:
    content = f"""<div class="page-header">
  <h1>通知设置</h1>
  <p>配置 TrendRadar 的新闻推送方式。当前仅展示邮件渠道。</p>
</div>

<div class="card">
  <div class="flex-between" style="margin-bottom:14px">
    <h2 style="margin-bottom:0">邮件配置</h2>
    <div style="display:flex;align-items:center;gap:8px">
      <span style="font-size:0.85rem;color:var(--text2)">启用通知</span>
      <label class="toggle"><input type="checkbox" id="notifEnabled" checked><span class="slider"></span></label>
    </div>
  </div>

  <div class="form-row">
    <div class="form-group"><label>发件人地址</label><input id="emailFrom" placeholder="your@email.com"></div>
    <div class="form-group"><label>密码 / 授权码</label><input id="emailPassword" type="password" placeholder="SMTP 密码或邮箱授权码"></div>
  </div>
  <div class="form-group"><label>收件人地址（多个用逗号分隔）</label><input id="emailTo" placeholder="recipient@email.com"></div>
  <div class="form-row">
    <div class="form-group"><label>SMTP 服务器（留空自动识别）</label><input id="emailSmtpServer" placeholder="留空则自动识别"></div>
    <div class="form-group"><label>SMTP 端口</label><input id="emailSmtpPort" placeholder="留空则自动识别"></div>
  </div>
  <p style="font-size:0.82rem;color:var(--text2);margin-bottom:14px">
    自动识别支持: Gmail、QQ邮箱、Outlook、163、126、新浪、搜狐、阿里云邮箱、Yandex、iCloud
  </p>
  <div class="btn-row"><button class="btn btn-primary" id="btnSave" onclick="saveConfig()">保存设置</button></div>
  <div id="status" class="status"></div>
</div>

<script>{NOTIFICATION_SCRIPT}</script>"""
    return _layout("通知设置", content, "notification")


# ═══════════════════════════════════════════════════════════════
# AI Settings
# ═══════════════════════════════════════════════════════════════

AI_SCRIPT = r"""
async function loadConfig() {
  try {
    const r = await fetch('/api/config/ai'); const d = await r.json();
    document.getElementById('aiModel').value = d.model || '';
    document.getElementById('aiApiKey').value = d.api_key || '';
    document.getElementById('aiApiBase').value = d.api_base || '';
    document.getElementById('aiTimeout').value = d.timeout || 120;
    document.getElementById('aiMaxTokens').value = d.max_tokens || 5000;
    document.getElementById('aiTemperature').value = d.temperature ?? 1.0;
    document.getElementById('aiAnalysisEnabled').checked = d.ai_analysis_enabled !== false;
    document.getElementById('aiTranslationEnabled').checked = d.ai_translation_enabled !== false;
    document.getElementById('aiFilterMethod').value = d.filter_method || 'ai';
    document.getElementById('articleContentEnabled').checked = d.article_content_enabled !== false;
  } catch(e) { showStatus('加载失败: ' + e.message, 'error'); }
}
async function saveConfig() {
  const btn = document.getElementById('btnSave'); btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> 保存中...';
  try {
    const data = {
      model: document.getElementById('aiModel').value.trim(),
      api_key: document.getElementById('aiApiKey').value.trim(),
      api_base: document.getElementById('aiApiBase').value.trim(),
      timeout: parseInt(document.getElementById('aiTimeout').value) || 120,
      max_tokens: parseInt(document.getElementById('aiMaxTokens').value) || 5000,
      temperature: parseFloat(document.getElementById('aiTemperature').value) ?? 1.0,
      ai_analysis_enabled: document.getElementById('aiAnalysisEnabled').checked,
      ai_translation_enabled: document.getElementById('aiTranslationEnabled').checked,
      filter_method: document.getElementById('aiFilterMethod').value,
      article_content_enabled: document.getElementById('articleContentEnabled').checked,
    };
    const r = await fetch('/api/config/ai', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data),
    });
    const d = await r.json();
    if (d.success) showStatus('AI 配置已保存', 'success');
    else showStatus('保存失败: ' + (d.error || '未知错误'), 'error');
  } catch(e) { showStatus('请求失败: ' + e.message, 'error'); }
  finally { btn.disabled = false; btn.innerHTML = '保存设置'; }
}
function showStatus(msg, type) {
  const el = document.getElementById('status');
  el.textContent = msg; el.className = 'status ' + type;
  setTimeout(() => { if (el.textContent === msg) el.className = 'status'; }, 5000);
}
loadConfig();
"""


def ai_page() -> str:
    content = f"""<div class="page-header">
  <h1>AI 设置</h1>
  <p>配置 AI 模型用于分析、筛选和翻译。基于 LiteLLM，支持 100+ 模型提供商。</p>
</div>

<div class="card">
  <h2>模型配置</h2>
  <div class="form-row">
    <div class="form-group"><label>模型（LiteLLM 格式）</label><input id="aiModel" placeholder="deepseek/deepseek-chat"></div>
    <div class="form-group"><label>API Key</label><input id="aiApiKey" type="password" placeholder="sk-..."></div>
  </div>
  <div class="form-group"><label>API Base URL（可选，自定义接口）</label><input id="aiApiBase" placeholder="留空使用默认地址"></div>
  <div class="form-row">
    <div class="form-group"><label>超时时间（秒）</label><input id="aiTimeout" type="number" value="120"></div>
    <div class="form-group"><label>最大 Token 数</label><input id="aiMaxTokens" type="number" value="5000"></div>
  </div>
  <div class="form-group"><label>Temperature (0.0 - 2.0)</label><input id="aiTemperature" type="number" step="0.1" min="0" max="2" value="1.0"></div>
</div>

<div class="card">
  <h2>功能开关</h2>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
    <div class="flex-between" style="background:var(--card2);padding:14px;border-radius:8px">
      <div><strong>AI 分析</strong><br><span style="font-size:0.82rem;color:var(--text2)">对新闻趋势进行深度分析</span></div>
      <label class="toggle"><input type="checkbox" id="aiAnalysisEnabled" checked><span class="slider"></span></label>
    </div>
    <div class="flex-between" style="background:var(--card2);padding:14px;border-radius:8px">
      <div><strong>AI 翻译</strong><br><span style="font-size:0.82rem;color:var(--text2)">将标题翻译为目标语言</span></div>
      <label class="toggle"><input type="checkbox" id="aiTranslationEnabled" checked><span class="slider"></span></label>
    </div>
    <div class="flex-between" style="background:var(--card2);padding:14px;border-radius:8px">
      <div><strong>正文抓取</strong><br><span style="font-size:0.82rem;color:var(--text2)">抓取完整文章正文生成摘要</span></div>
      <label class="toggle"><input type="checkbox" id="articleContentEnabled"><span class="slider"></span></label>
    </div>
    <div class="flex-between" style="background:var(--card2);padding:14px;border-radius:8px">
      <div><strong>筛选方式</strong><br>
        <select id="aiFilterMethod" style="width:auto;margin-top:4px">
          <option value="ai">AI 智能筛选</option>
          <option value="keyword">关键词筛选</option>
        </select>
      </div>
    </div>
  </div>
</div>

<div class="btn-row"><button class="btn btn-primary" id="btnSave" onclick="saveConfig()">保存设置</button></div>
<div id="status" class="status"></div>

<script>{AI_SCRIPT}</script>"""
    return _layout("AI 设置", content, "ai")