REACT_SYSTEM_PROMPT = r"""You are ${name}, and here is your profile:
${desc}
"""

REACT_TASK_PROMPT = r"""You are asked to complete the following TASK:
```
${task_description}
```
"""

REACT_APPEND_THOUGHT_PROMPT = r"""Now generate your thought without calling tools.
Return exactly one valid JSON object, with no Markdown fences and no text before or after it:
{"thought":"your thought"}
"""

REACT_APPEND_TOOL_PROMPT = r"""Now you must call the tools in this stage"""
