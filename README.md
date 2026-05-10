# 网页主题监控与 TrendRadar 集成服务

这个仓库基于 TrendRadar 的抓取、存储、报告和通知能力整理而来。当前项目保留原有热点聚合、RSS、AI 分析、MCP 查询等能力，同时把重点放在一个更直接的业务目标上：

> 用户提交网页链接、关注主题词和邮箱；系统定时检查网页更新，发现新增且命中主题词的文章后，抓取正文并通过邮件通知用户。

## 当前重点

- **单网页监控**：监控指定页面、RSS 或人民网栏目。
- **主题词匹配**：只通知与用户关注主题相关的新增文章。
- **正文抓取**：发现新文章后尽量抓取正文内容。
- **邮件通知**：将新增文章标题、链接和正文整理成 HTML 邮件发送。
- **Docker 部署**：支持容器内定时运行，也支持服务器端口配置。

## 保留能力

项目仍保留以下原有能力，后续可以按需要启用：

- 多平台热点聚合
- RSS 聚合
- AI 分析、AI 翻译、AI 筛选
- 多通知渠道：邮件、飞书、钉钉、企业微信、Telegram、ntfy、Bark、Slack 等
- 本地 SQLite 与 S3 兼容远程存储
- MCP 服务，用于让 AI 客户端查询和分析历史数据

## 最相关的代码

```text
trendradar/single_watch.py                  # 单网页监控主逻辑
trendradar/crawler/article_content.py       # 文章正文抓取
trendradar/crawler/people_cn.py             # 人民网栏目抓取
trendradar/notification/senders.py          # 邮件等通知发送
docker/docker-compose.single-watch.yml      # 单网页监控容器配置
docker/.env                                 # 部署环境变量
output/single_watch/                        # 单网页监控状态和邮件 HTML
```

## 单网页监控配置

常用环境变量：

```env
WATCH_URL=https://finance.people.com.cn/
WATCH_KEYWORDS=具身智能,机器人,人工智能
EMAIL_FROM=your_sender@example.com
EMAIL_PASSWORD=your_email_password_or_app_password
EMAIL_TO=user@example.com
EMAIL_SMTP_SERVER=smtp.example.com
EMAIL_SMTP_PORT=465
CHECK_INTERVAL=1800
```

说明：

- `WATCH_URL` 是要监控的网页或 RSS 地址。
- `WATCH_KEYWORDS` 支持逗号、分号或换行分隔。
- `EMAIL_FROM` 和 `EMAIL_PASSWORD` 是发信邮箱配置。
- `EMAIL_TO` 是收信邮箱。
- `CHECK_INTERVAL` 是检查间隔，单位秒。

## 主流程正文抓取

`cron/once` 主流程也支持文章正文抓取。开启后，系统会在生成 HTML 报告前，为命中的热榜/RSS 文章抓取正文；邮件通知使用同一份 HTML，因此邮件中也会包含正文摘录。

在 `docker/.env` 中开启：

```env
ARTICLE_CONTENT_ENABLED=true
ARTICLE_CONTENT_ONLY_NEW=true
ARTICLE_CONTENT_MAX_ARTICLES=10
ARTICLE_CONTENT_MAX_CHARS=4000
ARTICLE_CONTENT_USE_JINA=true
JINA_API_KEY=
```

说明：

- `ARTICLE_CONTENT_ONLY_NEW=true` 表示只抓本轮新增命中文章，适合邮件通知。
- `ARTICLE_CONTENT_ONLY_NEW=false` 表示抓报告里的命中文章，可能更慢。
- `ARTICLE_CONTENT_MAX_ARTICLES` 用来限制每轮最多抓几篇，避免定时任务跑太久。
- `ARTICLE_CONTENT_USE_JINA=true` 会优先用 Jina Reader 抽正文，失败后回退到本地 HTML 解析。

## 单网页监控 AI 摘要

单网页监控会先抓取文章正文，再尝试生成 AI 摘要。邮件中会优先展示“AI 摘要”，再展示“正文摘录”。如果未配置 `AI_API_KEY`，系统会自动跳过 AI 摘要，继续发送正文摘录。

```env
WATCH_AI_SUMMARY_ENABLED=true
AI_API_KEY=your_ai_api_key
AI_MODEL=deepseek/deepseek-chat
AI_API_BASE=
WATCH_AI_SUMMARY_MAX_INPUT_CHARS=6000
WATCH_AI_SUMMARY_MAX_TOKENS=700
```

## 本地运行

```bash
python -m trendradar --single-watch
```

循环监控：

```bash
python -m trendradar --single-watch-loop
```

测试邮件通知：

```bash
python -m trendradar --test-notification
```

配置体检：

```bash
python -m trendradar --doctor
```

## Docker 运行

进入 Docker 目录：

```bash
cd docker
```

单网页监控：

```bash
docker compose -f docker-compose.single-watch.yml up -d
```

完整服务：

```bash
docker compose up -d
```

本地构建：

```bash
docker compose -f docker-compose-build.yml up -d --build
```

服务器端口版本：

```bash
docker compose -f docker-compose.server.yml up -d
```

当前服务器端口约定：

- Web：`7000`
- MCP：`7001`

服务器容器名：

- 主服务：`trendradar-jjy`
- MCP 服务：`trendradar-mcp-jjy`

## 项目结构

详细结构说明见：

[项目结构说明](docs/项目结构说明.md)

## 后续重构方向

目前先保留完整功能，避免破坏已有能力。后续建议逐步做这些整理：

1. 把 `trendradar/__main__.py` 拆成更小的 CLI、运行器和诊断模块。
2. 把 `trendradar/single_watch.py` 中仍有价值的普通网页链接发现能力，逐步合并进主流程的数据源层。
3. 把邮件通知从多渠道通知中抽成更清晰的邮箱模块。
4. 增加多用户任务表、网页表单、任务启停和任务状态页面。

## 文档入口

根目录中几个 `README-*` 文件现在都作为当前项目的说明或索引使用。需要理解项目时，以本文件和 `docs/项目结构说明.md` 为准。
