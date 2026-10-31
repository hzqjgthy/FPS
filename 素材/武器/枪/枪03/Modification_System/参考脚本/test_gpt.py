#!/usr/bin/env python3
"""
gpt 接口 API 测试脚本
直接运行即可
"""

import json
import sys
import urllib.error
import urllib.request


URL = "https://gmn.chuangzuoli.com/v1/responses"
API_KEY = "sk-7f41772caa9d3c21fbbd8be472f6cd8444e651aaf09a7a6a807681d54ed621ae"
MODEL = "gpt-5.4"
TIMEOUT = 120
ENABLE_STREAM = True
DEVELOPER_PROMPT = "你是一个专业 AI 助手，请用简体中文准确回答问题。"
TEST_QUESTION = "测试问题：Python 的 list 和 tuple 有什么区别？请给 3 点并举一个简短示例。"


def extract_output_text(resp_json: dict) -> str:
    texts = []
    for item in resp_json.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if (
                isinstance(content, dict)
                and content.get("type") == "output_text"
                and isinstance(content.get("text"), str)
            ):
                texts.append(content["text"])
    return "\n".join(texts).strip()


def test_codex53_single_api() -> bool:
    print("=" * 60)
    print("测试 gpt Responses API（单接口）")
    print("=" * 60)
    print(f"URL: {URL}")
    print(f"模型: {MODEL}")
    print(f"流式输出: {ENABLE_STREAM}")
    print(f"问题: {TEST_QUESTION}")
    print("\n发送请求中...\n")

    payload = {
        "model": MODEL,
        "reasoning": {"effort": "xhigh"},
        "stream": ENABLE_STREAM,
        "input": [
            {
                "type": "message",
                "role": "developer",
                "content": [{"type": "input_text", "text": DEVELOPER_PROMPT}],
            },
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": TEST_QUESTION}],
            },
        ],
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream" if ENABLE_STREAM else "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "User-Agent": "python-requests/2.31.0",
    }

    request = urllib.request.Request(
        URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            if ENABLE_STREAM:
                print("📝 AI 回复 (流式):")
                print("-" * 60)
                full_text = []
                while True:
                    line = response.readline()
                    if not line:
                        break

                    line_text = line.decode("utf-8", errors="replace").strip()
                    if not line_text or line_text.startswith(":"):
                        continue

                    if not line_text.startswith("data: "):
                        continue

                    data_str = line_text[6:].strip()
                    if data_str == "[DONE]":
                        break

                    try:
                        event = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    if event.get("type") == "response.output_text.delta":
                        delta = event.get("delta", "")
                        if isinstance(delta, str) and delta:
                            print(delta, end="", flush=True)
                            full_text.append(delta)

                print("\n" + "-" * 60)
                if full_text:
                    print("✅ 流式测试成功")
                else:
                    print("⚠️ 流式响应中未提取到文本增量")
                return True

            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        print(f"❌ 请求失败，HTTP {exc.code}")
        print(exc.read().decode("utf-8", errors="replace"))
        return False
    except Exception as exc:
        print(f"❌ 请求出错: {exc}")
        return False

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print("❌ 响应不是 JSON")
        print(body)
        return False

    answer = extract_output_text(data)
    if answer:
        print("📝 AI 回复:")
        print("-" * 60)
        print(answer)
        print("-" * 60)
        print("✅ 测试成功")
        return True

    print("⚠️ 未提取到 output_text，打印完整响应:")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return True


def main() -> None:
    success = test_codex53_single_api()
    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
