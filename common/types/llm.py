from copy import deepcopy
import json
from pydantic import BaseModel
from openai.types.chat import ChatCompletionMessageToolCall
from common.utils.json_utils import JsonRepair


class LLMResult(BaseModel):
    content: None | str | dict = ""
    role: str = ""
    name: str = ""
    tool_calls: list[ChatCompletionMessageToolCall] | None = None
    parsed_tool_calls: list[ChatCompletionMessageToolCall] | None = None  # arguments are parsed into python objects
    tool_call_id: str | None = None
    send_tokens: int = 0
    recv_tokens: int = 0
    total_tokens: int = 0

    def __init__(self, **data):
        super().__init__(**data)
        if self.tool_calls:
            parsed_tool_calls = []

            for tool_call in self.tool_calls:
                tool_call_ = deepcopy(tool_call)
                tool_call_.function.arguments = json.loads(JsonRepair(tool_call_.function.arguments).repair())
                if tool_call_.function.arguments is None:
                    tool_call_.function.arguments = {}
                parsed_tool_calls.append(tool_call_)
            self.parsed_tool_calls = parsed_tool_calls

    def to_openai_message(self, add_name_prefix: bool = False):
        def _get_content():
            if add_name_prefix:
                return f"[{self.name}]: {self.content}"
            else:
                return self.content

        match self.role:
            # is user of system
            case "user" | "system":
                return {
                    "role": self.role,
                    "content": _get_content(),
                }
            case "assistant":
                result = {"role": self.role, "content": _get_content()}
                if self.tool_calls is not None:
                    result["tool_calls"] = self.tool_calls
                    # if "type" not in result["tool_calls"]:
                    #     result["tool_calls"]["type"] = "function"
                return result
            case "tool":
                return {
                    "role": self.role,
                    "content": _get_content(),
                    "tool_call_id": self.tool_call_id,
                }
            case _:
                raise ValueError(f"Invalid role: {self.role}")

    def __eq__(self, other):
        if not isinstance(other, LLMResult):
            return False
        result = True
        try:
            result &= self.content == other.content
        except Exception:
            try:
                result &= str(self.content) == str(self.content)
            except Exception:
                raise ValueError("The `content` field is not comparable")
        result &= self.role == other.role
        result &= self.name == other.name
        if self.tool_calls is not None or other.tool_calls is not None:
            result &= not (self.tool_calls is None or other.tool_calls is None)
            if not result:
                return False
            result &= len(self.tool_calls) == len(other.tool_calls)
            for t1, t2 in zip(self.tool_calls, other.tool_calls):
                result &= t1.id == t2.id
                result &= t1.function.arguments == t2.function.arguments
                result &= t1.function.name == t2.function.name
        if self.tool_call_id is not None or other.tool_call_id is not None:
            result &= not (self.tool_call_id is None or other.tool_call_id is None)
            if not result:
                return False
            result &= self.tool_call_id == other.tool_call_id
        return result

    def __hash__(self):
        return hash(
            (
                self.content,
                self.role,
                self.name,
                (
                    ((t.id, t.function.arguments, t.function.name) for t in self.tool_calls)
                    if self.tool_calls is not None
                    else tuple()
                ),
                self.tool_call_id,
            )
        )
