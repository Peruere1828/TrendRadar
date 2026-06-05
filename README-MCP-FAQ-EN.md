# MCP Notes

The MCP server gives AI clients tool-based access to TrendRadar data. The main workflow handles collection, filtering, reporting, and notifications; MCP is an optional query and analysis layer over the generated data.

## Layout

```text
mcp_server/
  server.py
  tools/
  services/
  utils/
```

## Capabilities

- Query collected news.
- Search by date, source, and keywords.
- Read article content.
- Analyze trends, co-occurrence, platform activity, and similar news.
- Check system status.
- Manage selected configuration and storage sync tasks.

## Docker

```bash
cd docker
docker compose up -d trendradar-mcp
```

Default local endpoint:

```text
http://127.0.0.1:3334/mcp
```

Server compose endpoint:

```text
http://127.0.0.1:3335/mcp
```

Chinese documentation is the primary reference:

[README-MCP-FAQ.md](README-MCP-FAQ.md)
