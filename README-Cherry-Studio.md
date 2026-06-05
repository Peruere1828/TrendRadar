# Cherry Studio / MCP 接入

Cherry Studio 可以通过 MCP 连接 TrendRadar，用来查询、读取和分析已抓取的数据。抓取、筛选、报告和通知仍由 TrendRadar 主流程执行。

## 启动 MCP

```bash
cd docker
docker compose up -d trendradar-mcp
```

默认本地地址：

```text
http://127.0.0.1:3334/mcp
```

服务器端口版本：

```text
http://127.0.0.1:3335/mcp
```

## 推荐使用场景

- 查询历史新闻。
- 按关键词、日期、平台检索。
- 读取已抓取文章内容。
- 让 AI 客户端生成趋势分析或摘要。
- 检查系统状态。

## 主流程

```text
config/config.yaml
  -> python -m trendradar
  -> trendradar/context.py 抓取、筛选、分析和生成报告
  -> trendradar/notification/ 推送通知
  -> output/ 保存运行产物
```

MCP 读取这些运行产物，不替代主流程。
