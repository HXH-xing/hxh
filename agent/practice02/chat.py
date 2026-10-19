"""带 Function Calling 的对话程序。

提供一个工具 getdate：通过调用本地 date 命令获取当前电脑的日期和时间
（使用子进程执行命令，而不是用 Python 的日期 API 取时间）。

使用说明:
    1. 安装依赖: pip install requests
    2. 修改同级目录 config.ini 中的 model / api_base / api_key
    3. 运行: python chat.py
"""
import configparser
import json
import os
import subprocess

import requests

CONFIG_PATH = "config.ini"

# 暴露给模型的工具定义
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "getdate",
            "description": "获取当前电脑的日期和时间",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "isLeapYear",
            "description": "判断给定年份是否为闰年",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "要判断的年份，例如 2024"}
                },
                "required": ["year"],
            },
        },
    },
]


def run_date_command() -> str:
    """调用本地 date 命令获取日期和时间（不写 Python 取时间的代码）。"""
    # Windows 的 date /t 只显示日期，配合 time /t 一起返回；其它系统直接用 date
    cmd = "date /t & time /t" if os.name == "nt" else "date"
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = (proc.stdout or "").strip() or (proc.stderr or "").strip()
    return output or "无法获取系统日期时间"


def is_leap_year(year: int) -> bool:
    """用 Python 代码判断闰年：能被 4 整除但不能被 100 整除，或能被 400 整除。"""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def execute_tool(name: str, arguments: str = "") -> str:
    """执行工具调用，返回结果字符串。"""
    args = json.loads(arguments) if arguments else {}
    if name == "getdate":
        return run_date_command()
    if name == "isLeapYear":
        year = int(args["year"])
        return f"{year} 年是闰年" if is_leap_year(year) else f"{year} 年不是闰年"
    return f"未知工具: {name}"


def main():
    # 1. 读取配置
    config = configparser.ConfigParser()
    if not config.read(CONFIG_PATH, encoding="utf-8"):
        print(f"未找到配置文件 {CONFIG_PATH}")
        return
    model = config.get("llm", "model")
    api_base = config.get("llm", "api_base")
    api_key = config.get("llm", "api_key")
    max_tokens = config.getint("llm", "max_tokens")

    messages = [
        {"role": "system", "content": "你是一个助手。询问日期或时间时调用 getdate 工具；询问某年是否为闰年时调用 isLeapYear 工具。"}
    ]

    print("带工具调用的对话已启动（输入 exit 退出）")
    while True:
        try:
            question = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue

        messages.append({"role": "user", "content": question})

        # 2. 交给模型，可能触发多次工具调用
        while True:
            try:
                resp = requests.post(
                    f"{api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": messages,
                        "tools": TOOLS,
                        "max_tokens": max_tokens,
                        "stream": False,
                    },
                    timeout=60,
                )
                resp.raise_for_status()
                message = resp.json()["choices"][0]["message"]
            except requests.RequestException as e:
                print(f"请求失败: {e}")
                break
            except (KeyError, IndexError):
                print("返回格式异常")
                break

            tool_calls = message.get("tool_calls")
            if not tool_calls:
                print("\nAI:", message.get("content"))
                messages.append({"role": "assistant", "content": message.get("content") or ""})
                break

            # 3. 执行模型请求的工具，并把结果回传
            messages.append(message)
            for call in tool_calls:
                name = call["function"]["name"]
                result = execute_tool(name, call["function"].get("arguments"))
                print(f"[调用工具] {name} -> {result}")
                messages.append(
                    {"role": "tool", "tool_call_id": call["id"], "content": result}
                )


if __name__ == "__main__":
    main()
