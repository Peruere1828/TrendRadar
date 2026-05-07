# MCP 说明

MCP 不是当前“网页更新后发邮件”需求的主路径，但项目仍然保留 MCP 服务，方便后续让 AI 客户端查询和分析已抓取的数据。

## MCP 在本项目里的定位

```text
mcp_server/
  server.py               # MCP HTTP/stdio 服务入口
  tools/                  # 暴露给 AI 客户端的工具
  services/               # 数据、解析、缓存服务
  utils/                  # 参数校验、日期解析、错误类型
```

MCP 适合做这些事：

- 查询历史新闻数据。
- 根据关键词、日期或来源分析趋势。
- 读取已抓取文章。
- 检查系统状态。
- 触发部分管理或同步操作。

## 什么时候不需要 MCP

如果你只需要：

- 用户提交网页链接。
- 用户填写主题词。
- 用户留下邮箱。
- 网页有新增相关文章时发送邮件。

那么优先关注：

```text
trendradar/single_watch.py
trendradar/crawler/article_content.py
trendradar/notification/senders.py
docker/docker-compose.single-watch.yml
```

## Docker 启动 MCP

```bash
cd docker
docker compose up -d trendradar-mcp
```

服务器约定端口：

```text
http://服务器地址:3335/mcp
```

本地默认端口通常是：

```text
http://127.0.0.1:3333/mcp
```

## 后续整理建议

后续如果继续重构，建议把 `mcp_server/` 迁入更清晰的 `trendradar/mcp/` 或保持独立包，但需要在文档里明确它是“查询分析服务”，不是网页监控主流程。
