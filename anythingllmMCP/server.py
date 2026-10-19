"""AnythingLLM MCP 服务（Streamable HTTP）。

只提供一个工具：列出 AnythingLLM 的所有工作区（slug）。
运行:
    pip install -r requirements.txt
    python server.py
默认监听 http://0.0.0.0:8691/mcp

环境变量（均可选）:
    ANYTHINGLLM_BASE     AnythingLLM 地址，默认 http://localhost:3001/api/v1
    ANYTHINGLLM_API_KEY  API Key
    MCP_PORT             MCP 端口，默认 8691
"""
import os

import httpx
from mcp.server import MCPServer

ANYTHINGLLM_BASE = os.getenv("ANYTHINGLLM_BASE", "http://localhost:3001/api/v1")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY", "YOUR_API_KEY_HERE")
MCP_PORT = int(os.getenv("MCP_PORT", "8691"))

mcp = MCPServer("anythingllm")


@mcp.tool()
async def list_workspaces() -> str:
    """列出 AnythingLLM 的所有工作区，返回名称和 slug。"""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{ANYTHINGLLM_BASE}/workspaces",
            headers={"Authorization": f"Bearer {ANYTHINGLLM_API_KEY}"},
        )
        resp.raise_for_status()
    workspaces = resp.json().get("workspaces", [])
    if not workspaces:
        return "没有找到任何工作区"
    return "工作区列表:\n" + "\n".join(
        f"- {w.get('name')} (slug: {w.get('slug')})" for w in workspaces
    )


def main():
    mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
