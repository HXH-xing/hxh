# AnythingLLM MCP Server

把 AnythingLLM 封装成一个 MCP 工具（Streamable HTTP），只有一个工具：列出所有工作区（slug）。

## 运行

```bash
pip install -r requirements.txt
python server.py
```

MCP 端点：`http://localhost:8691/mcp`

## 客户端配置

```json
{
  "mcpServers": {
    "anythingllm": {
      "url": "http://localhost:8691/mcp"
    }
  }
}
```

## 环境变量（可选）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ANYTHINGLLM_BASE` | `http://localhost:3001/api/v1` | AnythingLLM 地址 |
| `ANYTHINGLLM_API_KEY` | `YOUR_API_KEY_HERE` | API Key |
| `MCP_PORT` | `8691` | MCP 端口 |

## 工具

### `list_workspaces`

列出 AnythingLLM 的所有工作区，返回 `name` 与 `slug`。
