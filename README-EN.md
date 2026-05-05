# Project Notes

This repository is now maintained as a web page topic monitoring service built on top of the retained TrendRadar capabilities.

The main product goal is:

> A user provides a web page URL, topic keywords, and an email address. The service checks the page periodically, detects new related articles, extracts article content, and sends an email notification.

For day-to-day development, use the Chinese documentation as the source of truth:

- [README.md](README.md)
- [项目结构说明](docs/项目结构说明.md)

Key files:

```text
trendradar/single_watch.py
trendradar/crawler/article_content.py
trendradar/crawler/people_cn.py
trendradar/notification/senders.py
docker/docker-compose.single-watch.yml
docker/.env
```

Retained optional capabilities include hot list aggregation, RSS, AI analysis, notification channels, local/remote storage, and MCP. They are not the first path for the current web monitoring requirement.
