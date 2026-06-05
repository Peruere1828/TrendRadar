# TrendRadar

TrendRadar is a news aggregation, filtering, reporting, and notification service. It collects hot-list and RSS news, filters items with keywords or AI interests, renders HTML reports, and sends notifications through email and other channels.

## Features

- Hot-list source collection.
- RSS/Atom feed collection.
- Keyword filtering with grouped frequency words.
- AI interest filtering with LiteLLM-compatible models.
- AI analysis and translation.
- Article content extraction for matched hot-list and RSS items.
- HTML report generation.
- Email, Feishu, DingTalk, WeCom, Telegram, ntfy, Bark, Slack, and generic webhook notifications.
- Web management pages for status, sources, RSS, filters, notifications, and AI settings.
- MCP server for AI-client data queries and analysis.

## Main Files

```text
trendradar/__main__.py                    # CLI and main workflow
trendradar/context.py                     # workflow orchestration
trendradar/webserver.py                   # web server and APIs
trendradar/web_pages.py                   # web page templates
trendradar/crawler/fetcher.py             # hot-list crawler entry
trendradar/crawler/rss/                   # RSS fetching and parsing
trendradar/crawler/article_content.py     # article content extraction
trendradar/ai/                            # AI client, analysis, filter, translation
trendradar/report/                        # report generation
trendradar/notification/                  # notification rendering and sending
mcp_server/                               # MCP server
```

## Configuration

Primary configuration files:

```text
config/config.yaml
config/timeline.yaml
config/frequency_words.txt
config/ai_interests.txt
docker/.env.example
```

Create a local Docker environment file before deployment:

```bash
cp docker/.env.example docker/.env
```

`docker/.env` is local-only and should not be committed.

## Run Locally

```bash
python -m trendradar
python -m trendradar --show-schedule
python -m trendradar --doctor
python -m trendradar --test-notification
```

## Run With Docker

```bash
cd docker
docker compose up -d
docker compose -f docker-compose-build.yml up -d --build
docker compose -f docker-compose.server.yml up -d
```

Default endpoints:

```text
Web: http://localhost:9999
MCP: http://127.0.0.1:3334/mcp
```

Server compose endpoints:

```text
Web: http://server-address:7000
MCP: http://127.0.0.1:3335/mcp
```

## Web Pages

```text
/              Home
/dashboard     Status
/platforms     Platform sources
/rss           RSS feeds
/filter        Keyword and AI-interest filtering
/notification  Notification settings
/ai            AI settings
/my_interest   AI interest editor
/files         Output file browser
```

## Output

`output/` contains runtime databases and reports. It is ignored by Git and should be persisted by the deployment environment.

Chinese documentation is the primary project reference:

[README.md](README.md)
