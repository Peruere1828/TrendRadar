# MCP 说明

MCP 服务用于让 AI 客户端查询和分析 TrendRadar 已抓取的数据。主流程不依赖 MCP；主流程负责抓取、筛选、报告和通知，MCP 负责对已有数据提供工具化访问。

## 目录

```text
mcp_server/
  server.py               # MCP HTTP/stdio 服务入口
  tools/                  # 暴露给 AI 客户端的工具
  services/               # 数据、解析、缓存服务
  utils/                  # 参数校验、日期解析、错误类型
```

## 能力

- 查询已抓取新闻。
- 按日期、来源、关键词检索数据。
- 读取文章内容。
- 分析趋势、共现词、平台活跃度和相似新闻。
- 检查系统状态。
- 管理部分配置和存储同步任务。

## Docker 启动

```bash
cd docker
docker compose up -d trendradar-mcp
```

默认本地地址：

```text
http://127.0.0.1:3334/mcp
```

服务器端口版本：

```bash
docker compose -f docker-compose.server.yml up -d trendradar-mcp
```

服务器 compose 内部约定：

```text
http://127.0.0.1:3335/mcp
```

## 与主流程的关系

主流程入口是：

```text
trendradar/__main__.py
trendradar/context.py
```

MCP 读取主流程产生的数据和配置，不负责定时抓取，也不负责发送通知。
