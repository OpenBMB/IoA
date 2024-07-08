from httpx import Cookies
from pydantic import BaseModel
from common.types.llm import LLMResult


class ToolResponse(BaseModel):
    observation: str = ""
    cookies: Cookies = None

    class Config:
        arbitrary_types_allowed = True

    def to_llm_result(self, tool_call_id: str = "0") -> LLMResult:
        return LLMResult(
            content=self.observation,
            role="tool",
            tool_call_id=tool_call_id,
        )
