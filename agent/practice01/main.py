"""极简一次性对话：读取 config.ini -> 输入一次问题 -> 调用 LLM -> 打印回答（不保存历史）

使用说明:
    1. 安装依赖: pip install requests
    2. 修改 config.ini 中的 model / api_base / api_key
    3. 运行: python main.py
"""
import configparser

import requests

CONFIG_PATH = "config.ini"


def main():
    # 1. 读取配置
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding="utf-8")
    model = config.get("llm", "model")
    api_base = config.get("llm", "api_base")
    api_key = config.get("llm", "api_key")
    max_tokens = config.getint("llm", "max_tokens")

    # 2. 接收用户一次性输入
    prompt = input("请输入问题（单次对话，不保存历史）: ")

    # 3. 调用 LLM 接口（非流式，一次性取完整返回）
    try:
        resp = requests.post(
            f"{api_base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],  # 只带当前问题，不带历史
                "max_tokens": max_tokens,
                "stream": False,
            },
            timeout=60,
        )
        resp.raise_for_status()  # HTTP 错误抛异常
        answer = resp.json()["choices"][0]["message"]["content"]

        # 4. 打印结果
        print("\n回答:")
        print(answer)
    except requests.RequestException as e:
        print(f"请求失败: {e}")
    except (KeyError, IndexError):
        print("返回格式异常，未找到回答内容")


if __name__ == "__main__":
    main()
