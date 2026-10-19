"""宠物医院 MCP 服务（Streamable HTTP）。

把 pethospital.exe 暴露的 REST API 封装成 MCP 工具。

运行:
    pip install -r requirements.txt
    python server.py
默认监听 http://127.0.0.1:8000/mcp

环境变量:
    PETHOSPITAL_BASE  宠物医院服务地址，默认 http://127.0.0.1:8080
    MCP_HOST / MCP_PORT / MCP_PATH  MCP 监听配置
"""
import os
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

BASE = os.getenv("PETHOSPITAL_BASE", "http://127.0.0.1:8080").rstrip("/")
_client = httpx.AsyncClient(base_url=BASE, timeout=30.0)

mcp = MCPServer(
    "pet-hospital",
    version="1.0.0",
    instructions="宠物医院管理系统：宠物档案增删改查、全文检索、病历、收费与经营统计。",
)


async def _api(method: str, path: str, **kwargs: Any) -> Any:
    """调用医院 REST 接口，成功时返回响应里的 data 字段。"""
    try:
        resp = await _client.request(method, path, **kwargs)
    except httpx.HTTPError as exc:
        raise ToolError(f"无法连接宠物医院服务({BASE}): {exc}") from exc
    try:
        body = resp.json()
    except ValueError:
        raise ToolError(f"HTTP {resp.status_code}: {resp.text[:300]}")
    if resp.status_code >= 400:
        raise ToolError(f"HTTP {resp.status_code}: {body.get('message', body)}")
    return body.get("data", body)


def _params(**kw: Any) -> dict[str, Any]:
    """去掉值为 None 的查询参数。"""
    return {k: v for k, v in kw.items() if v is not None}


@mcp.tool(description="查询宠物列表，可按种类/就诊状态/医生/疾病/主人姓名/主人电话过滤，支持分页和排序。")
async def list_pets(
    species: str | None = None,
    status: str | None = None,
    doctor: str | None = None,
    disease: str | None = None,
    owner_name: str | None = None,
    owner_phone: str | None = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "createdAt",
    order: str = "desc",
) -> Any:
    """status 取值: 待就诊/治疗中/住院中/已康复/慢性病随访；sort_by 可用 id,name,ownerName,species,doctor,disease,status,totalCost,visitCount,createdAt,updatedAt；order 为 asc/desc。"""
    return await _api(
        "GET",
        "/api/v1/pets",
        params=_params(
            species=species,
            status=status,
            doctor=doctor,
            disease=disease,
            ownerName=owner_name,
            ownerPhone=owner_phone,
            page=page,
            pageSize=page_size,
            sortBy=sort_by,
            order=order,
        ),
    )


@mcp.tool(description="按 ID 查询单个宠物完整档案（含历史病历 records 和消费明细 charges）。")
async def get_pet(pet_id: str) -> Any:
    return await _api("GET", f"/api/v1/pets/{pet_id}")


@mcp.tool(description="新增宠物档案。pet 字段示例: {name, species, breed, gender, ageMonths, ownerName, ownerPhone, doctor, disease, status}。")
async def create_pet(pet: dict[str, Any]) -> Any:
    return await _api("POST", "/api/v1/pets", json=pet)


@mcp.tool(description="局部更新宠物档案，changes 只需传要修改的字段，例如 {\"status\":\"已康复\"}。")
async def update_pet(pet_id: str, changes: dict[str, Any]) -> Any:
    return await _api("PATCH", f"/api/v1/pets/{pet_id}", json=changes)


@mcp.tool(description="按 ID 删除宠物档案。")
async def delete_pet(pet_id: str) -> Any:
    return await _api("DELETE", f"/api/v1/pets/{pet_id}")


@mcp.tool(description="全文检索宠物，跨字段空格分词（AND），例如 \"金毛 肠胃炎\"。")
async def search_pets(keyword: str) -> Any:
    return await _api("GET", "/api/v1/pets/search", params={"q": keyword})


@mcp.tool(description="为宠物追加一条历史病历。record 字段: {doctor, diagnosis, symptoms, treatment, prescription:[...], weightKg, temperature, followUp, charge}。")
async def add_record(pet_id: str, record: dict[str, Any]) -> Any:
    return await _api("POST", f"/api/v1/pets/{pet_id}/records", json=record)


@mcp.tool(description="为宠物追加一笔收费（自动累加到总花费）。charge 字段: {item, category, amount, doctor}。")
async def add_charge(pet_id: str, charge: dict[str, Any]) -> Any:
    return await _api("POST", f"/api/v1/pets/{pet_id}/charges", json=charge)


@mcp.tool(description="查询单只宠物的费用与就诊汇总。")
async def get_pet_summary(pet_id: str) -> Any:
    return await _api("GET", f"/api/v1/pets/{pet_id}/summary")


@mcp.tool(description="医院经营统计（总收入/物种分布/医生排行），top 控制排行条数。")
async def get_stats(top: int = 5) -> Any:
    return await _api("GET", "/api/v1/stats", params={"top": top})


@mcp.tool(description="获取枚举字典：宠物种类、就诊状态、收费分类、可选字段。")
async def get_meta() -> Any:
    return await _api("GET", "/api/v1/meta")


if __name__ == "__main__":
    mcp.run(
        "streamable-http",
        host=os.getenv("MCP_HOST", "127.0.0.1"),
        port=int(os.getenv("MCP_PORT", "8000")),
        streamable_http_path=os.getenv("MCP_PATH", "/mcp"),
    )
