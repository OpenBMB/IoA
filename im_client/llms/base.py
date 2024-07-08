from abc import abstractmethod

from pydantic import BaseModel, Field

from common.types.llm import LLMResult


class BaseModelArgs(BaseModel):
    pass


class BaseLLM(BaseModel):
    args: BaseModelArgs = Field(default_factory=BaseModelArgs)
    max_retry: int = Field(default=3)

    @abstractmethod
    def get_spend(self) -> float:
        """
        Number of USD spent
        """
        return -1.0

    # @abstractmethod
    # def generate_response(self, **kwargs) -> LLMResult:
    #     pass

    @abstractmethod
    async def agenerate_response(self, **kwargs) -> LLMResult:
        pass


class BaseChatModel(BaseLLM):
    pass


class BaseCompletionModel(BaseLLM):
    pass
