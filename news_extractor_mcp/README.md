# News Extractor MCP Server

English | [简体中文](README.zh-CN.md)

Model Context Protocol (MCP) server that exposes the multi-platform news extractor from this repository to AI assistants over the **Streamable HTTP transport**. It provides four tools (`extract_news`, `batch_extract_news`, `detect_news_platform`, `list_supported_platforms`) backed by the shared `news_extractor_core` package.

---

## Requirements

- Python 3.10 or newer
- [`uv`](https://github.com/astral-sh/uv) for dependency management
- Access to this repository (the MCP server runs locally)

Install dependencies:

```bash
cd /path/to/NewsCrawler/news_extractor_mcp
uv sync
```

Start the Streamable HTTP server (default host `127.0.0.1`, port `8765`, path `/mcp`):

```bash
uv run server.py --host 127.0.0.1 --port 8765
```

The MCP endpoint is reachable at `http://127.0.0.1:8765/mcp` (use `--path` to override). A simple health probe is available at `http://127.0.0.1:8765/health`.

---

## Client Integration (Streamable HTTP)

All clients should point to the Streamable HTTP endpoint (default `http://127.0.0.1:8765/mcp`). Configuration keys differ per implementation; the snippets below follow each tool’s current documentation.

### Cursor

Update `~/.cursor/mcp.json` (or project-level `.cursor/mcp.json`):

No explicit transport type is required; the URL alone is sufficient.

```json
{
  "mcpServers": {
    "news-extractor": {
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

Reload MCP servers or restart Cursor, then include `use news-extractor` in prompts.

### Claude Code (Anthropic)

Using the CLI:

```bash
claude mcp add --transport http news-extractor http://127.0.0.1:8765/mcp
```

Manual config (`~/.claude/mcp/tool_config.json`):

```json
{
  "name": "news-extractor",
  "type": "http",
  "url": "http://127.0.0.1:8765/mcp"
}
```

Restart Claude Code after editing.

### Gemini CLI

Edit `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "news-extractor": {
      "httpUrl": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

Restart `gemini chat` to pick up the new server.

### Generic CLI / Other Clients

For Streamable-HTTP-aware clients (VS Code, Windsurf, Cline, Qwen Coder, etc.), point the HTTP URL to `http://127.0.0.1:8765/mcp`. Refer to the client’s documentation for the exact property names (some use `url`, others `httpUrl` or `type: "streamableHttp"`). If a client only supports stdio, run a bridge (e.g. [smithery](https://smithery.ai)) or the MCP reference proxy.

---

## Available Tools

| Tool                       | Description                               |
|----------------------------|-------------------------------------------|
| `extract_news`             | Fetch a single article and return JSON/MD |
| `batch_extract_news`       | Extract multiple URLs with success stats  |
| `detect_news_platform`     | Detect the platform for a URL             |
| `list_supported_platforms` | List the 9 supported platforms            |

All responses share a consistent envelope:

```json
{
  "status": "success",
  "...": "payload"
}
```

---

## Development Notes

- Business logic lives in `news_extractor_core`; keep new adapters there.
- The SSE app mounts `/sse` for the stream and `/messages/` for client POSTs—adjust paths in `server.py` if you need custom routing.
- Run `uv run python -m compileall news_extractor_mcp` for a fast syntax check before sharing the server.
