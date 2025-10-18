# 新闻提取 MCP 服务器

[English](README.md) | 简体中文

基于 Model Context Protocol (MCP) 的新闻提取服务器，通过 **Streamable HTTP** 传输将本仓库的多平台新闻抓取能力暴露给各类 AI 助手。服务器提供四个工具：`extract_news`、`batch_extract_news`、`detect_news_platform`、`list_supported_platforms`，底层逻辑来自共享的 `news_extractor_core` 包。

---

## 环境要求

- Python 3.10 或以上版本  
- 已安装 [`uv`](https://github.com/astral-sh/uv) 依赖管理工具  
- 能访问此仓库（需要本地运行服务器）

安装依赖：

```bash
cd /path/to/NewsCrawler/news_extractor_mcp
uv sync
```

启动 Streamable HTTP 服务器（默认主机 `127.0.0.1`，端口 `8765`，路径 `/mcp`）：

```bash
uv run server.py --host 127.0.0.1 --port 8765
```

- 服务器会提供以下端点：
- MCP 入口: `http://127.0.0.1:8765/mcp`（如需自定义可使用 `--path` 参数）
- 健康检查: `http://127.0.0.1:8765/health`

---

## 主流客户端集成（Streamable HTTP）

不同客户端的字段名称略有差异，但都需要指向上面的 MCP 入口（默认 `http://127.0.0.1:8765/mcp`）。以下示例可按需替换主机与端口。

### Cursor

1. 打开 `~/.cursor/mcp.json`（或项目目录下的 `.cursor/mcp.json`）。  
2. 在 `mcpServers` 中添加：

```json
{
  "mcpServers": {
    "news-extractor": {
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

保存后重启 Cursor 或刷新 MCP 列表，即可在对话提示中加入 `use news-extractor` 强制调用工具。

### Claude Code（Anthropic）

Claude Code 提供 CLI 来管理 MCP 连接：

```bash
claude mcp add --transport http news-extractor http://127.0.0.1:8765/mcp
```

若需手动编辑 `~/.claude/mcp/tool_config.json`（路径视系统而定），可写入：

```json
{
  "name": "news-extractor",
  "type": "http",
  "url": "http://127.0.0.1:8765/mcp"
}
```

重启 Claude Code 后即可生效。

### Gemini CLI

1. 打开 `~/.gemini/settings.json`（如不存在请新建）。  
2. 在 `mcpServers` 字段中添加：

```json
{
  "mcpServers": {
    "news-extractor": {
      "httpUrl": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

重新启动 `gemini chat` 后即可在命令中附带 `use news-extractor` 使用该服务器。

### 通用 CLI / 其他 MCP 客户端

任意支持 Streamable HTTP 的 MCP 客户端（VS Code、Windsurf、Qwen Coder、Cline 等）均可将 URL 指向 `http://127.0.0.1:8765/mcp`（部分客户端需要设置 `type: "streamableHttp"` 或 `httpUrl` 字段）。若客户端仅支持 stdio，可参考 [smithery](https://smithery.ai) 或官方 MCP 代理做转接。

---

## 工具列表

| 工具名称                    | 功能说明                          |
|----------------------------|-----------------------------------|
| `extract_news`             | 抓取单篇文章，返回 JSON/Markdown |
| `batch_extract_news`       | 批量抓取多个链接并输出统计       |
| `detect_news_platform`     | 判断链接所属新闻平台             |
| `list_supported_platforms` | 列出当前支持的 9 个平台          |

---

## 开发与调试提示

- 核心能力集中在 `news_extractor_core`，新增平台请优先在该包内维护适配器。
- Streamable HTTP 默认路径为 `/mcp`，可在 `server.py` 中调整。
- 提交前可执行 `uv run python -m compileall news_extractor_mcp` 做基础语法检查。
