"""带本地文件操作工具（Function Calling）的对话程序。

在 chat.py 的基础上新增一组本地文件/目录操作的 function call：
    get_current_directory  获取当前工作目录
    list_directory         列出指定目录下的所有文件和子目录
    get_file_type          获取指定文件的类型
    read_file              读取纯文本文件内容
    create_file            按目录+文件名创建新文件
    edit_file              编辑纯文本文件内容
    create_directory       创建新目录
    delete_directory       删除目录（含非空目录）
    delete_file            删除文件
    rename_path            重命名文件或目录

使用说明:
    1. 安装依赖: pip install requests
    2. 修改同级目录 config.ini 中的 model / api_base / api_key
    3. 运行: python tool.py
"""
import configparser
import json
import mimetypes
import os
import shutil
import subprocess

import requests

CONFIG_PATH = "config.ini"

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
                "properties": {"year": {"type": "integer", "description": "要判断的年份，例如 2024"}},
                "required": ["year"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_directory",
            "description": "获取当前工作目录",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "列出指定目录下的所有文件和子目录",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "目录路径"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_type",
            "description": "获取指定文件的类型（目录/纯文本文件/二进制文件，含扩展名与 MIME）",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "文件或目录路径"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取指定文件的内容（仅支持纯文本格式文件）",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "文件路径"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "在指定目录下按文件名创建新文件，可写入初始内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "目标目录"},
                    "file_name": {"type": "string", "description": "文件名，例如 note.txt"},
                    "content": {"type": "string", "description": "文件初始内容，可留空"},
                },
                "required": ["directory", "file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "编辑指定纯文本文件的内容（覆盖写入新内容）",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "新的文件内容"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_directory",
            "description": "创建新目录（父目录不存在会自动创建）",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "目录路径"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_directory",
            "description": "删除目录，包括非空目录",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "目录路径"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "删除指定文件",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "文件路径"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rename_path",
            "description": "重命名文件或目录",
            "parameters": {
                "type": "object",
                "properties": {
                    "old_path": {"type": "string", "description": "原路径"},
                    "new_path": {"type": "string", "description": "新路径"},
                },
                "required": ["old_path", "new_path"],
            },
        },
    },
]


# ---------- 基础工具 ----------

def run_date_command() -> str:
    """调用本地 date 命令获取日期和时间。"""
    cmd = "date /t & time /t" if os.name == "nt" else "date"
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = (proc.stdout or "").strip() or (proc.stderr or "").strip()
    return output or "无法获取系统日期时间"


def is_leap_year(year: int) -> bool:
    """用 Python 代码判断闰年：能被 4 整除但不能被 100 整除，或能被 400 整除。"""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


# ---------- 本地文件操作工具 ----------

def is_plain_text(path: str) -> bool:
    """判断文件是否为纯文本（无空字节且可用 UTF-8 解码）。"""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return False
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def get_current_directory() -> str:
    return os.getcwd()


def list_directory(path: str) -> str:
    if not os.path.isdir(path):
        return f"错误：目录不存在 {path}"
    entries = sorted(os.listdir(path), key=str.lower)
    if not entries:
        return f"目录 {path} 为空"
    lines = [f"[目录] {name}" if os.path.isdir(os.path.join(path, name)) else f"[文件] {name}" for name in entries]
    return f"目录: {path}\n" + "\n".join(lines) + f"\n共 {len(entries)} 项"


def get_file_type(path: str) -> str:
    if not os.path.exists(path):
        return f"错误：路径不存在 {path}"
    if os.path.isdir(path):
        return f"{path}\n类型: 目录"
    ext = os.path.splitext(path)[1] or "无"
    mime, _ = mimetypes.guess_type(path)
    kind = "纯文本文件" if is_plain_text(path) else "二进制/其他文件"
    return f"{path}\n扩展名: {ext}\nMIME: {mime or '未知'}\n类型: {kind}"


def read_file(path: str) -> str:
    if not os.path.isfile(path):
        return f"错误：文件不存在 {path}"
    if not is_plain_text(path):
        return f"错误：{path} 不是纯文本格式文件，无法读取"
    with open(path, "r", encoding="utf-8") as f:
        return f.read() or "(空文件)"


def create_file(directory: str, file_name: str, content: str = "") -> str:
    path = os.path.join(directory, file_name)
    if os.path.exists(path):
        return f"错误：文件已存在 {path}"
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已创建文件 {path}（{len(content)} 字符）"


def edit_file(path: str, content: str) -> str:
    if not os.path.isfile(path):
        return f"错误：文件不存在 {path}"
    if not is_plain_text(path):
        return f"错误：{path} 不是纯文本格式文件，无法编辑"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已更新文件 {path}（现 {len(content)} 字符）"


def create_directory(path: str) -> str:
    if os.path.exists(path):
        return f"错误：路径已存在 {path}"
    os.makedirs(path)
    return f"已创建目录 {path}"


def delete_directory(path: str) -> str:
    if not os.path.isdir(path):
        return f"错误：目录不存在 {path}"
    shutil.rmtree(path)
    return f"已删除目录 {path}（含其中所有内容）"


def delete_file(path: str) -> str:
    if not os.path.isfile(path):
        return f"错误：文件不存在 {path}"
    os.remove(path)
    return f"已删除文件 {path}"


def rename_path(old_path: str, new_path: str) -> str:
    if not os.path.exists(old_path):
        return f"错误：路径不存在 {old_path}"
    if os.path.exists(new_path):
        return f"错误：目标路径已存在 {new_path}"
    os.rename(old_path, new_path)
    return f"已重命名 {old_path} -> {new_path}"


def execute_tool(name: str, arguments: str = "") -> str:
    """执行工具调用，返回结果字符串。"""
    args = json.loads(arguments) if arguments else {}
    try:
        if name == "getdate":
            return run_date_command()
        if name == "isLeapYear":
            year = int(args["year"])
            return f"{year} 年是闰年" if is_leap_year(year) else f"{year} 年不是闰年"
        if name == "get_current_directory":
            return get_current_directory()
        if name == "list_directory":
            return list_directory(args["path"])
        if name == "get_file_type":
            return get_file_type(args["path"])
        if name == "read_file":
            return read_file(args["path"])
        if name == "create_file":
            return create_file(args["directory"], args["file_name"], args.get("content", ""))
        if name == "edit_file":
            return edit_file(args["path"], args["content"])
        if name == "create_directory":
            return create_directory(args["path"])
        if name == "delete_directory":
            return delete_directory(args["path"])
        if name == "delete_file":
            return delete_file(args["path"])
        if name == "rename_path":
            return rename_path(args["old_path"], args["new_path"])
        return f"未知工具: {name}"
    except OSError as e:
        return f"操作失败: {e}"


def main():
    config = configparser.ConfigParser()
    if not config.read(CONFIG_PATH, encoding="utf-8"):
        print(f"未找到配置文件 {CONFIG_PATH}")
        return
    model = config.get("llm", "model")
    api_base = config.get("llm", "api_base")
    api_key = config.get("llm", "api_key")
    max_tokens = config.getint("llm", "max_tokens")

    messages = [
        {
            "role": "system",
            "content": "你是一个助手，可以调用工具完成本地文件操作、获取日期时间和判断闰年。",
        }
    ]

    print("本地文件操作对话已启动（输入 exit 退出）")
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

            messages.append(message)
            for call in tool_calls:
                name = call["function"]["name"]
                result = execute_tool(name, call["function"].get("arguments"))
                print(f"[调用工具] {name} -> {result}")
                messages.append(
                    {"role": "tool", "tool_call_id": call["id"], "content": str(result)}
                )


if __name__ == "__main__":
    main()
