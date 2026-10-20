#!/usr/bin/env python3
import json
import sys

import requests

IOA_URL = "http://127.0.0.1:5050/launch_goal"

GOAL = """请完成一个三类异构 Agent 协作的数据分析任务。所有数据均为虚构测试数据：

2025 年三个实验室每季度用电量（MWh）：
- 北区：Q1 120，Q2 135，Q3 142，Q4 158
- 东区：Q1 98，Q2 110，Q3 105，Q4 126
- 南区：Q1 150，Q2 154，Q3 168，Q4 180

分工：
1. AutoGPT 负责分配以下两项工作，等待两位成员各回复一次，然后整合结果。不要联网或调用浏览器、终端、文件工具。
2. Open Interpreter 只用一段简短 Python 代码计算各实验室全年总量、总合计、全体 Q1 与 Q4 总量，以及各实验室和全体的 Q1 到 Q4 增长率。只在内存中计算，不读写文件；代码不要包含 Markdown 代码围栏；计算一次后把数值和公式回复给 AutoGPT。
3. ReAct Agent 不调用工具，独立手算并复核全年总量、全体 Q1/Q4 总量及增长率，并回复计算过程。

增长率按 (Q4-Q1)/Q1×100% 计算，保留一位小数。
最终用中文输出全年总量降序表格、全体 Q1/Q4 总量及增长率、各实验室增长率、复核是否一致和一句结论。成员未实际参与或结果不一致时如实说明。只用题目数据，不重复计算或扩展任务。"""

payload = {
    "goal": GOAL,
    "team_member_names": ["AutoGPT", "Open Interpreter", "ReAct Agent"],
    "max_turns": 6,
}

response = None

try:
    response = requests.post(IOA_URL, json=payload, timeout=(10, 1200))
    print("HTTP", response.status_code)
    response.raise_for_status()
    result = response.json()

except json.JSONDecodeError:
    body = response.text[:2000] if response is not None else "<无响应正文>"
    print("IoA 返回的内容不是有效 JSON：", body, file=sys.stderr)
    sys.exit(1)

except requests.Timeout as exc:
    print(
        f"IoA 请求等待超时：{exc}\n"
        "任务可能仍在服务端运行；先查看容器日志，不要立刻重复提交。",
        file=sys.stderr,
    )
    sys.exit(2)

except requests.HTTPError as exc:
    body = response.text[:2000] if response is not None else "<无响应正文>"
    print(f"IoA HTTP 错误：{exc}\n响应正文：{body}", file=sys.stderr)
    sys.exit(1)

except requests.RequestException as exc:
    print(f"IoA 请求失败：{exc}", file=sys.stderr)
    sys.exit(1)

if isinstance(result, list) and len(result) >= 2:
    print("会话 ID：", result[0])
    print("任务回答：\n", result[1])
else:
    print(json.dumps(result, ensure_ascii=False, indent=2))
