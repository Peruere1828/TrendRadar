# Cherry Studio / MCP 接入说明

这个文件只保留当前项目需要的最小说明。Cherry Studio 这类 MCP 客户端可以连接本项目的 MCP 服务，用来查询和分析已抓取的数据。

如果你的目标只是“网页有新增相关文章就发邮件”，不需要配置 Cherry Studio。

## 启动 MCP 服务

```bash
cd docker
docker compose up -d trendradar-mcp
```

本地地址：

```text
http://127.0.0.1:3333/mcp
```

服务器地址按当前约定：

```text
http://服务器地址:3335/mcp
```

## 推荐关注

当前网页监控主流程仍然是：

```text
用户提交链接、主题词、邮箱
  -> single_watch.py 定时检查
  -> article_content.py 抓正文
  -> senders.py 发邮件
```

MCP 只作为额外的查询分析入口保留。
