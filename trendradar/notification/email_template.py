# coding=utf-8
"""
邮件专用 HTML 模板

生成邮件客户端兼容的 HTML 通知，与浏览器端 HTML 报告（report/html.py）独立。
设计原则：
- table 布局 + inline style（邮件兼容）
- 最大宽度 600px，单列响应式
- 无 JavaScript、无外部资源、无 Web 字体
- 图标用 emoji 代替
"""

from datetime import datetime
from typing import Dict, List, Optional

from trendradar.report.helpers import html_escape


def render_email_html(
    report_data: Dict,
    report_type: str,
    now: datetime,
    rss_items: Optional[List[Dict]] = None,
    rss_new_items: Optional[List[Dict]] = None,
) -> str:
    """生成邮件安全的 HTML 通知

    Args:
        report_data: 报告数据 {"stats": [...], "new_titles": [...], ...}
        report_type: 报告类型（如 "全天汇总"）
        now: 当前时间
        rss_items: RSS 统计条目（可选）
        rss_new_items: RSS 新增条目（可选）

    Returns:
        邮件兼容的 HTML 字符串
    """

    stats = report_data.get("stats", [])
    new_titles = report_data.get("new_titles", [])
    total_new_count = report_data.get("total_new_count", 0)

    total_matched = sum(len(stat.get("titles", [])) for stat in stats)
    keyword_names = [stat["word"] for stat in stats[:8]]

    top_picks = _extract_top_picks(stats, max_picks=5)

    parts = []
    parts.append(_render_header(report_type, now, total_matched, keyword_names))

    if top_picks:
        parts.append(_render_top_picks(top_picks))

    if stats:
        parts.append(_render_stats_sections(stats))

    if new_titles and total_new_count > 0:
        parts.append(_render_new_section(new_titles, total_new_count))

    if rss_items:
        parts.append(_render_rss_sections(rss_items))

    if rss_new_items:
        parts.append(_render_rss_sections(rss_new_items, title="RSS 新增更新"))

    parts.append(_render_footer())

    body = "\n".join(parts)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TrendRadar 热点速报</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f4f4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:#f4f4f4;">
<tr>
<td align="center" style="padding:16px 12px;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600" style="max-width:600px;width:100%;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
{body}
</table>
</td>
</tr>
</table>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════
# 内部渲染函数
# ═══════════════════════════════════════════════════════════════════


def _clean_article_summary(text: str, title: str = "", max_chars: int = 200) -> str:
    """将文章正文或 RSS 摘要清理为邮件中可用的简短概述"""
    if not text:
        return ""
    lines = text.strip().split("\n")
    cleaned = []
    title_clean = title.strip().lower()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower() == title_clean:
            continue
        if any(stripped.startswith(p) for p in ("首页", "Home", "导航", "当前位置")):
            continue
        if ">" in stripped and len(stripped) < 40:
            continue
        cleaned.append(stripped)
    result = " ".join(cleaned)
    return result[:max_chars]


def _extract_top_picks(stats: List[Dict], max_picks: int = 5) -> List[Dict]:
    """从各主题中提取排名最高的条目作为 Top Picks"""
    candidates = []
    for stat in stats:
        keyword = stat["word"]
        for title_data in stat.get("titles", []):
            ranks = title_data.get("ranks", [])
            min_rank = min(ranks) if ranks else 99
            ac = title_data.get("article_content", "")
            sm = title_data.get("summary", "")
            raw_summary = ac or sm
            clean_summary = _clean_article_summary(raw_summary, title_data.get("title", ""))
            candidates.append({
                "keyword": keyword,
                "title": title_data["title"],
                "source_name": title_data.get("source_name", ""),
                "url": title_data.get("mobile_url") or title_data.get("mobileUrl") or title_data.get("url", ""),
                "ranks": ranks,
                "min_rank": min_rank,
                "time_display": title_data.get("time_display", ""),
                "count": title_data.get("count", 1),
                "summary": clean_summary,
                "is_new": title_data.get("is_new", False),
            })

    candidates.sort(key=lambda x: x["min_rank"])
    return candidates[:max_picks]


def _rank_color(ranks: List[int]) -> str:
    if not ranks:
        return "#6b7280"
    min_rank = min(ranks)
    if min_rank <= 3:
        return "#dc2626"
    elif min_rank <= 10:
        return "#ea580c"
    return "#6b7280"


def _rank_badge(ranks: List[int]) -> str:
    if not ranks:
        return ""
    min_r = min(ranks)
    max_r = max(ranks)
    color = _rank_color(ranks)
    text = str(min_r) if min_r == max_r else f"{min_r}-{max_r}"
    return (
        f'<span style="display:inline-block;background-color:{color};'
        f'color:#fff;font-size:10px;font-weight:700;padding:1px 6px;'
        f'border-radius:8px;vertical-align:middle;">#{text}</span>'
    )


def _render_header(
    report_type: str,
    now: datetime,
    total_matched: int,
    keyword_names: List[str],
) -> str:
    date_str = now.strftime("%m月%d日")
    time_str = now.strftime("%H:%M")
    kw_tags = " · ".join(keyword_names) if keyword_names else "暂无匹配"

    return f"""<tr>
<td style="background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:28px 24px;text-align:center;color:#ffffff;">
    <div style="font-size:22px;font-weight:700;margin:0 0 8px 0;">TrendRadar 热点速报</div>
    <div style="font-size:13px;opacity:0.85;margin:0 0 12px 0;">{date_str} · {report_type} · {time_str}</div>
    <div style="font-size:14px;opacity:0.9;margin:0 0 8px 0;">今日匹配 <strong>{total_matched}</strong> 条热点，覆盖 <strong>{len(keyword_names)}</strong> 个话题</div>
    <div style="font-size:13px;opacity:0.75;">{kw_tags}</div>
</td>
</tr>"""


def _render_top_picks(picks: List[Dict]) -> str:
    lines = [
        '<tr><td style="padding:20px 24px 8px 24px;">',
        '<div style="font-size:15px;font-weight:700;color:#1a1a1a;margin:0 0 4px 0;">'
        '你可能最关心的 Top Picks</div>',
        '<div style="font-size:12px;color:#9ca3af;">排名最高的热点文章</div>',
        "</td></tr>",
    ]

    for pick in picks:
        badge = _rank_badge(pick["ranks"])
        new_badge = (
            ' <span style="display:inline-block;background:linear-gradient(135deg,#f43f5e,#ec4899);'
            'color:#fff;font-size:9px;font-weight:600;padding:1px 5px;border-radius:3px;'
            'vertical-align:middle;">NEW</span>'
            if pick["is_new"]
            else ""
        )

        title_html = html_escape(pick["title"])
        keyword_html = html_escape(pick["keyword"])
        source_html = html_escape(pick["source_name"]) if pick.get("source_name") else ""
        time_html = html_escape(pick["time_display"]) if pick.get("time_display") else ""

        summary = pick.get("summary", "")
        summary_html = ""
        if summary:
            summary_html = (
                f'<div style="font-size:13px;color:#6b7280;line-height:1.5;margin:8px 0 0 0;">'
                f'{html_escape(summary[:200])}'
                f'</div>'
            )

        url = pick.get("url", "")
        link_html = ""
        if url:
            link_html = (
                f'<div style="margin-top:8px;">'
                f'<a href="{html_escape(url)}" target="_blank" '
                f'style="color:#4f46e5;text-decoration:none;font-size:12px;font-weight:500;">'
                f'查看原文 &rarr;</a>'
                f'</div>'
            )

        border_color = _rank_color(pick["ranks"])

        meta_parts = []
        if source_html:
            meta_parts.append(source_html)
        if time_html:
            meta_parts.append(time_html)
        meta_line = " · ".join(meta_parts)

        lines.append(f"""<tr>
<td style="padding:8px 24px;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
 style="background-color:#fafafa;border-left:3px solid {border_color};border-radius:0 8px 8px 0;">
<tr>
<td style="padding:14px 16px;">
    <div style="margin-bottom:4px;">
        {badge}{new_badge}
        <span style="font-size:11px;color:#6b7280;margin-left:6px;">[{keyword_html}]</span>
        {f'<span style="font-size:11px;color:#9ca3af;margin-left:6px;">{meta_line}</span>' if meta_line else ''}
    </div>
    <div style="font-size:15px;font-weight:600;color:#1a1a1a;line-height:1.4;">
        {title_html}
    </div>
    {summary_html}
    {link_html}
</td>
</tr>
</table>
</td>
</tr>""")

    return "\n".join(lines)


def _render_stats_sections(stats: List[Dict]) -> str:
    lines = [
        '<tr><td style="padding:24px 24px 8px 24px;">',
        '<div style="font-size:15px;font-weight:700;color:#1a1a1a;margin:0 0 4px 0;">全部匹配文章</div>',
        '<div style="font-size:12px;color:#9ca3af;">按你关注的话题分组</div>',
        "</td></tr>",
    ]

    for stat in stats:
        word = html_escape(stat["word"])
        count = stat["count"]
        titles = stat.get("titles", [])

        lines.append(f"""<tr>
<td style="padding:16px 24px 4px 24px;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
<tr>
<td style="padding:10px 14px;background-color:#eef2ff;border-radius:8px;">
    <span style="font-size:15px;font-weight:600;color:#4f46e5;">{word}</span>
    <span style="font-size:13px;color:#6b7280;margin-left:8px;">{count} 条</span>
</td>
</tr>
</table>
</td>
</tr>""")

        line_items = []
        for j, td in enumerate(titles, 1):
            title = html_escape(td["title"])
            source = html_escape(td.get("source_name", ""))
            url = td.get("mobile_url") or td.get("url", "")
            ranks = td.get("ranks", [])
            badge = _rank_badge(ranks) if ranks else ""
            is_new = td.get("is_new", False)
            new_mark = (
                ' <span style="display:inline-block;background:#fbbf24;color:#92400e;'
                'font-size:9px;font-weight:700;padding:1px 5px;border-radius:3px;'
                'vertical-align:middle;">NEW</span>'
                if is_new
                else ""
            )
            summary = _clean_article_summary(td.get("article_content") or td.get("summary", ""), td.get("title", ""), 150)
            summary_line = ""
            if summary:
                summary_line = (
                    f'<div style="font-size:12px;color:#9ca3af;line-height:1.4;margin-top:2px;">'
                    f'{html_escape(summary)}'
                    f'</div>'
                )

            title_cell = (
                f'<a href="{html_escape(url)}" target="_blank" '
                f'style="color:#1a1a1a;text-decoration:none;font-size:14px;line-height:1.4;">'
                f'{title}</a>'
                if url
                else f'<span style="color:#1a1a1a;font-size:14px;">{title}</span>'
            )

            line_items.append(f"""<tr>
<td style="padding:8px 14px;border-bottom:1px solid #f5f5f5;">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
    <tr>
        <td style="width:24px;vertical-align:top;padding-top:2px;">
            <span style="display:inline-block;width:20px;height:20px;line-height:20px;
            text-align:center;background-color:#f3f4f6;border-radius:50%;font-size:11px;
            color:#9ca3af;font-weight:600;">{j}</span>
        </td>
        <td style="vertical-align:top;">
            <div>
                {badge}{new_mark}
                {f'<span style="font-size:11px;color:#9ca3af;margin-left:4px;">{source}</span>' if source else ''}
            </div>
            {title_cell}
            {summary_line}
        </td>
    </tr>
    </table>
</td>
</tr>""")

        lines.append(f"""<tr>
<td style="padding:0 24px;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
 style="background-color:#ffffff;border-radius:8px;border:1px solid #f0f0f0;">
{"".join(line_items)}
</table>
</td>
</tr>""")

    return "\n".join(lines)


def _render_new_section(new_titles: List[Dict], total_new_count: int) -> str:
    lines = [
        '<tr><td style="padding:24px 24px 8px 24px;">',
        '<div style="border-top:2px solid #e5e7eb;margin-bottom:16px;"></div>',
        f'<div style="font-size:15px;font-weight:700;color:#1a1a1a;margin:0 0 4px 0;">'
        f'本次新增热点 (共 {total_new_count} 条)</div>',
        '<div style="font-size:12px;color:#9ca3af;">本轮爬取新出现的热点文章</div>',
        "</td></tr>",
    ]

    for source_data in new_titles:
        source_name = html_escape(source_data.get("source_name", ""))
        titles = source_data.get("titles", [])
        lines.append(f"""<tr>
<td style="padding:12px 24px 4px 24px;">
    <span style="font-size:13px;font-weight:600;color:#6b7280;">{source_name} · {len(titles)}条</span>
</td>
</tr>""")

        for td in titles:
            title = html_escape(td["title"])
            url = td.get("mobile_url") or td.get("url", "")
            ranks = td.get("ranks", [])
            badge = _rank_badge(ranks) if ranks else ""
            title_cell = (
                f'<a href="{html_escape(url)}" target="_blank" '
                f'style="color:#1a1a1a;text-decoration:none;font-size:14px;">{title}</a>'
                if url
                else f'<span style="color:#1a1a1a;font-size:14px;">{title}</span>'
            )
            lines.append(f"""<tr>
<td style="padding:6px 24px 6px 38px;">
    {badge} {title_cell}
</td>
</tr>""")

    return "\n".join(lines)


def _render_rss_sections(
    rss_items: List[Dict],
    title: str = "RSS 订阅更新",
) -> str:
    if not rss_items:
        return ""

    total = sum(stat.get("count", 0) for stat in rss_items)

    lines = [
        '<tr><td style="padding:24px 24px 8px 24px;">',
        '<div style="border-top:2px solid #e5e7eb;margin-bottom:16px;"></div>',
        f'<div style="font-size:15px;font-weight:700;color:#059669;margin:0 0 4px 0;">'
        f'{title}</div>',
        f'<div style="font-size:12px;color:#9ca3af;">共 {total} 条</div>',
        "</td></tr>",
    ]

    for stat in rss_items:
        keyword = html_escape(stat.get("word", ""))
        titles = stat.get("titles", [])

        lines.append(f"""<tr>
<td style="padding:12px 24px 4px 24px;">
    <span style="font-size:13px;font-weight:600;color:#059669;">{keyword} · {len(titles)}条</span>
</td>
</tr>""")

        for td in titles:
            title_text = html_escape(td["title"])
            source = html_escape(td.get("source_name", ""))
            url = td.get("url", "")
            time_display = td.get("time_display", "")
            summary = _clean_article_summary(td.get("article_content") or td.get("summary", ""), td.get("title", ""), 150)
            is_new = td.get("is_new", False)
            new_mark = (
                ' <span style="color:#dc2626;font-size:10px;font-weight:700;">NEW</span>'
                if is_new
                else ""
            )

            title_cell = (
                f'<a href="{html_escape(url)}" target="_blank" '
                f'style="color:#1a1a1a;text-decoration:none;font-size:14px;font-weight:500;">'
                f'{title_text}</a>'
                if url
                else f'<span style="color:#1a1a1a;font-size:14px;font-weight:500;">{title_text}</span>'
            )

            meta_parts = []
            if time_display:
                meta_parts.append(html_escape(time_display))
            if source:
                meta_parts.append(source)
            meta_line = " · ".join(meta_parts)

            summary_html = ""
            if summary:
                summary_html = (
                    f'<div style="font-size:12px;color:#6b7280;line-height:1.5;margin-top:4px;">'
                    f'{html_escape(summary[:200])}'
                    f'</div>'
                )

            lines.append(f"""<tr>
<td style="padding:8px 24px;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"
 style="background-color:#f0fdf4;border-left:3px solid #10b981;border-radius:0 8px 8px 0;">
<tr>
<td style="padding:10px 14px;">
    <div style="margin-bottom:2px;">
        <span style="font-size:11px;color:#6b7280;">{meta_line}</span>{new_mark}
    </div>
    {title_cell}
    {summary_html}
</td>
</tr>
</table>
</td>
</tr>""")

    return "\n".join(lines)


def _render_footer() -> str:
    return """<tr>
<td style="padding:24px;text-align:center;background-color:#f8f9fa;border-top:1px solid #e5e7eb;">
    <div style="font-size:12px;color:#9ca3af;line-height:1.6;">
        由 <span style="font-weight:600;color:#6b7280;">TrendRadar</span> 生成 ·
        <a href="https://github.com/sansan0/TrendRadar" target="_blank"
           style="color:#4f46e5;text-decoration:none;font-weight:500;">GitHub 开源项目</a>
    </div>
</td>
</tr>"""


def render_email_plain_text(
    report_data: Dict,
    report_type: str,
    now: datetime,
    rss_items: Optional[List[Dict]] = None,
) -> str:
    """生成纯文本备选内容"""
    stats = report_data.get("stats", [])
    total_matched = sum(len(stat.get("titles", [])) for stat in stats)
    date_str = now.strftime("%Y-%m-%d %H:%M")

    lines = [
        "TrendRadar 热点速报",
        "=" * 40,
        f"报告类型：{report_type}",
        f"生成时间：{date_str}",
        f"匹配热点：{total_matched} 条",
        "",
    ]

    top_picks = _extract_top_picks(stats, max_picks=5)
    if top_picks:
        lines.append("─ Top Picks ─")
        for i, pick in enumerate(top_picks, 1):
            ranks_str = f"#{min(pick['ranks'])}" if pick["ranks"] else ""
            new_mark = " [NEW]" if pick["is_new"] else ""
            lines.append(f"  {i}. [{pick['keyword']}] {pick['title']}{new_mark}")
            if pick.get("source_name"):
                lines.append(f"     来源：{pick['source_name']} {ranks_str}")
            if pick.get("summary"):
                lines.append(f"     摘要：{pick['summary'][:200]}")
            if pick.get("url"):
                lines.append(f"     链接：{pick['url']}")
            lines.append("")

    if stats:
        lines.append("─ 全部匹配文章 ─")
        for stat in stats:
            lines.append(f"\n  [{stat['word']}] ({stat['count']} 条)")
            for j, td in enumerate(stat.get("titles", []), 1):
                source = td.get("source_name", "")
                ranks = td.get("ranks", [])
                rank_str = f" #{min(ranks)}" if ranks else ""
                new_mark = " [NEW]" if td.get("is_new") else ""
                url = td.get("mobile_url") or td.get("url", "")
                lines.append(f"    {j}. {td['title']}{new_mark}")
                if source:
                    lines.append(f"       {source}{rank_str}")
                if url:
                    lines.append(f"       {url}")
                summary = _clean_article_summary(td.get("article_content") or td.get("summary", ""), td.get("title", ""), 150)
                if summary:
                    lines.append(f"       {summary[:200]}")

    if rss_items:
        lines.append("")
        lines.append("─ RSS 订阅更新 ─")
        for stat in rss_items:
            lines.append(f"\n  [{stat.get('word', '')}] ({stat.get('count', 0)} 条)")
            for td in stat.get("titles", []):
                time_str = f" {td.get('time_display', '')}" if td.get("time_display") else ""
                lines.append(f"    · {td['title']}{time_str}")
                if td.get("url"):
                    lines.append(f"      {td['url']}")
                summary = _clean_article_summary(td.get("article_content") or td.get("summary", ""), td.get("title", ""), 150)
                if summary:
                    lines.append(f"      {summary[:200]}")

    lines.append("")
    lines.append("─" * 40)
    lines.append("由 TrendRadar 生成 · https://github.com/sansan0/TrendRadar")

    return "\n".join(lines)


def build_subject(
    report_data: Dict,
    report_type: str,
    now: datetime,
) -> str:
    """构建动态邮件主题行

    根据匹配热度自动选择格式：
    - 高热度（>=20条）：🔥「关键词」等N个话题有M条新热点
    - 中热度（>=5条）：📊 关键词×12 关键词×8 · TrendRadar 速报
    - 低热度：📋 今日热点涉及你关注的关键词
    """
    stats = report_data.get("stats", [])
    total_matched = sum(len(stat.get("titles", [])) for stat in stats)

    sorted_stats = sorted(stats, key=lambda x: len(x.get("titles", [])), reverse=True)
    top3 = sorted_stats[:3]

    if total_matched >= 20:
        first_word = top3[0]["word"] if top3 else ""
        topic_count = len(stats)
        return f"🔥「{first_word}」等{topic_count}个话题有{total_matched}条新热点 · TrendRadar"

    elif total_matched >= 5:
        parts = []
        for stat in top3:
            count = len(stat.get("titles", []))
            parts.append(f"{stat['word']}×{count}")
        kw_part = " ".join(parts)
        return f"📊 {kw_part} · TrendRadar 速报"

    elif total_matched > 0:
        kw_list = "、".join(s["word"] for s in top3[:2])
        return f"📋 今日热点涉及「{kw_list}」· TrendRadar"

    else:
        return f"TrendRadar · {now.strftime('%m月%d日')} {report_type}"
