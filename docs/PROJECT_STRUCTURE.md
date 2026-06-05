# Project Structure

Current project structure:

```text
TrendRadar/
  trendradar/              # main application package
  mcp_server/              # MCP query and analysis service
  config/                  # runtime configuration and prompts
  docker/                  # Dockerfiles, Compose files, entrypoint scripts
  docs/                    # documentation and static docs site
  output/                  # generated runtime data, ignored by Git
  _image/                  # documentation image assets
```

Main workflow:

```text
python -m trendradar
  -> load config/config.yaml and environment variables
  -> resolve schedule from config/timeline.yaml
  -> collect hot-list and RSS news
  -> filter by keywords or AI interests
  -> fetch article content for matched items when enabled
  -> render reports
  -> send notifications
  -> write output/
```

Important modules:

```text
trendradar/__main__.py                    # CLI and workflow entry
trendradar/context.py                     # workflow orchestration
trendradar/webserver.py                   # web server and config APIs
trendradar/web_pages.py                   # web page templates
trendradar/crawler/                       # hot-list, RSS, source, article fetchers
trendradar/ai/                            # AI client, analysis, filtering, translation
trendradar/report/                        # report generation
trendradar/notification/                  # notification rendering and sending
trendradar/storage/                       # local SQLite and S3-compatible storage
mcp_server/                               # MCP server and tools
```

Chinese documentation is the primary reference:

[项目结构说明.md](项目结构说明.md)
