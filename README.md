# 智汇 TrendRadar

智汇 TrendRadar 是一个新闻聚合、筛选、报告和通知服务。它从热榜平台和 RSS 源抓取资讯，按关键词或 AI 兴趣描述筛选重点内容，生成 HTML 报告，并通过邮件、飞书、钉钉、企业微信、Telegram、ntfy、Bark、Slack 等渠道推送。

## 功能

- 热榜平台抓取：通过 `config/config.yaml` 配置平台来源。
- RSS 聚合：支持 RSS/Atom 订阅源抓取和报告展示。
- 关键词筛选：使用 `config/frequency_words.txt` 做分组关键词匹配。
- AI 筛选：使用 `config/ai_interests.txt` 的自然语言兴趣描述生成标签并分类资讯。
- AI 分析与翻译：基于 LiteLLM 接入模型服务。
- 正文抓取：为命中的热榜/RSS 文章抓取正文摘录，并写入报告。
- 多渠道通知：统一生成报告后发送到已配置渠道。
- Web 管理页：查看状态、管理平台/RSS/筛选/通知/AI 配置。
- MCP 服务：供 AI 客户端查询和分析历史数据。

## 目录

```text
trendradar/              # 主程序代码
mcp_server/              # MCP 查询分析服务
config/                  # 运行配置、关键词、AI 提示词
docker/                  # Docker 镜像、Compose、入口脚本
docs/                    # 项目说明和静态文档站点
output/                  # 运行产物，本地生成，不提交到仓库
_image/                  # 文档图片素材
```

## 关键模块

```text
trendradar/__main__.py                    # CLI 和主流程入口
trendradar/context.py                     # 抓取、筛选、分析、通知编排
trendradar/webserver.py                   # Web 管理服务和 API
trendradar/web_pages.py                   # Web 管理页面模板
trendradar/crawler/fetcher.py             # 热榜抓取入口
trendradar/crawler/rss/                   # RSS 抓取与解析
trendradar/crawler/article_content.py     # 文章正文抓取
trendradar/ai/                            # AI 客户端、分析、筛选、翻译
trendradar/report/                        # 报告数据与 HTML 渲染
trendradar/notification/                  # 通知内容渲染和发送
trendradar/storage/                       # 本地 SQLite 与 S3 兼容远程存储
```

## 配置

主要配置文件：

```text
config/config.yaml              # 平台、RSS、通知、AI、存储、正文抓取等主配置
config/timeline.yaml            # 调度时间线
config/frequency_words.txt      # 关键词分组
config/ai_interests.txt         # AI 兴趣描述
config/ai_filter/               # AI 筛选提示词
docker/.env.example             # Docker 环境变量示例
```

本地部署时复制一份环境变量文件：

```bash
cp docker/.env.example docker/.env
```

常用环境变量：

```env
WEBSERVER_PORT=9999
RUN_MODE=cron
IMMEDIATE_RUN=true

EMAIL_FROM=
EMAIL_PASSWORD=
EMAIL_TO=
EMAIL_SMTP_SERVER=
EMAIL_SMTP_PORT=

AI_API_KEY=
AI_MODEL=
AI_API_BASE=

ARTICLE_CONTENT_ENABLED=false
ARTICLE_CONTENT_ONLY_NEW=true
ARTICLE_CONTENT_MAX_ARTICLES=10
ARTICLE_CONTENT_USE_JINA=true
JINA_API_KEY=
```

`docker/.env` 是本地私有配置文件，不提交到仓库。

## 本地运行

安装依赖后执行主流程：

```bash
python -m trendradar
```

查看调度状态：

```bash
python -m trendradar --show-schedule
```

运行配置体检：

```bash
python -m trendradar --doctor
```

测试通知渠道：

```bash
python -m trendradar --test-notification
```

## Docker 运行

进入 Docker 目录：

```bash
cd docker
```

使用现有镜像运行：

```bash
docker compose up -d
```

本地构建运行：

```bash
docker compose -f docker-compose-build.yml up -d --build
```

服务器端口版本：

```bash
docker compose -f docker-compose.server.yml up -d
```

默认访问地址：

```text
Web: http://localhost:9999
MCP: http://127.0.0.1:3334/mcp
```

`docker-compose.server.yml` 约定：

```text
Web: http://服务器地址:7000
MCP: http://127.0.0.1:3335/mcp
```

## Web 管理页

Web 服务由 `trendradar/webserver.py` 提供，页面包括：

```text
/              首页
/dashboard     系统状态
/platforms     平台源配置
/rss           RSS 源配置
/filter        关键词和 AI 兴趣筛选配置
/notification  通知配置
/ai            AI 配置
/my_interest   AI 兴趣描述配置
/files         输出文件浏览
```

对应 API 会直接读写 `config/config.yaml`、`config/frequency_words.txt` 和 `config/ai_interests.txt`。

## 运行产物

`output/` 存放数据库、HTML 报告等运行产物。该目录不提交到仓库，部署时建议挂载到宿主机或持久化存储。

## MCP

MCP 服务位于 `mcp_server/`，用于让 AI 客户端查询历史新闻、读取文章、分析趋势、检查系统状态和触发部分管理操作。MCP 不是主流程运行的必要条件。

更多结构说明见：

[docs/项目结构说明.md](docs/项目结构说明.md)
