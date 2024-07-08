REACT_SYSTEM_PROMPT = r"""You are ${name}, and here is your profile:
${desc}
"""

REACT_TASK_PROMPT = r"""You are asked to complete the following TASK:
```
${task_description}
```
"""

REACT_APPEND_THOUGHT_PROMPT = r"""Now you must generate your thought and you must not call the tools in this stage. You should respond in the following json format:
```json
{
    "thought": "your thought"
}
```"""

REACT_APPEND_TOOL_PROMPT = r"""Now you must call the tools in this stage"""
