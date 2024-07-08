from abc import abstractmethod
from typing import List

from pydantic import BaseModel

from common.types.llm import LLMResult


class BaseMemory(BaseModel):
    @abstractmethod
    def add_messages(self, messages: LLMResult | List[LLMResult]) -> None:
        pass

    @abstractmethod
    def to_string(self) -> str:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

    def to_messages(self) -> List[dict]:
        pass
