# 宠物医院 MCP

把宠物医院服务（`pethospital.exe`）的 REST API 封装为 MCP 工具，采用 **Streamable HTTP** 传输，单文件实现（`server.py`）。

## 安装与运行

```powershell
pip install -r requirements.txt
# 先启动宠物医院服务（默认 http://127.0.0.1:8080）
python server.py
```

启动后 MCP 端点为 `http://127.0.0.1:8000/mcp`。

可配置环境变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `PETHOSPITAL_BASE` | `http://127.0.0.1:8080` | 宠物医院服务地址 |
| `MCP_HOST` | `127.0.0.1` | MCP 监听地址 |
| `MCP_PORT` | `8000` | MCP 监听端口 |
| `MCP_PATH` | `/mcp` | MCP 路径 |

## 接入客户端

在支持 Streamable HTTP 的 MCP 客户端里配置：

```json
{
  "mcpServers": {
    "pet-hospital": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

## 工具列表

| 工具 | 说明 |
| --- | --- |
| `list_pets` | 宠物列表，支持种类/状态/医生/疾病/主人姓名/电话过滤 + 分页排序 |
| `get_pet` | 按 ID 查完整档案（含病历与消费明细） |
| `create_pet` | 新增宠物档案 |
| `update_pet` | 局部更新（只传要改的字段） |
| `delete_pet` | 删除宠物档案 |
| `search_pets` | 全文检索（空格分词 AND） |
| `add_record` | 追加历史病历 |
| `add_charge` | 追加一笔收费（自动累计总花费） |
| `get_pet_summary` | 单只宠物费用与就诊汇总 |
| `get_stats` | 医院经营统计 |
| `get_meta` | 枚举字典（种类/状态/收费分类） |
