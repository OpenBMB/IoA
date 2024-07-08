import json
import os
from copy import deepcopy
from typing import List, Optional, Union
from uuid import uuid4

import aiofiles
import numpy as np
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
from pydantic import Field
from tenacity import retry, stop_after_attempt, wait_exponential

from common.log import logger
from common.types.llm import LLMResult
from common.utils.json_utils import JsonRepair
from common.utils.misc import log_retry

from . import LOCAL_LLMS, llm_registry
from .base import BaseChatModel, BaseModelArgs

try:
    import openai
    from openai._types import NOT_GIVEN, NotGiven
    from openai.types.chat import ChatCompletion

    async_openai_client = openai.AsyncClient()
    sync_openai_client = openai.Client()
except ImportError:
    is_openai_available = False
    logger.warn("openai package is not installed")
else:
    if os.environ.get("OPENAI_API_KEY") is None and os.environ.get("AZURE_OPENAI_API_KEY") is None:
        logger.warn("OPENAI_API_KEY is not set. OpenAI models will not be available.")
    if os.environ.get("AZURE_OPENAI_API_KEY") is not None:
        openai.api_type = "azure"
        openai.api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        openai.base_url = os.environ.get("AZURE_OPENAI_BASE_URL")
        openai.api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")

OPENAI_RESPONSE_LOG_PATH = os.environ.get("OPENAI_RESPONSE_LOG_PATH", "")


async def async_write_to_file(data: dict, filename: str):
    os.makedirs(OPENAI_RESPONSE_LOG_PATH, exist_ok=True)
    file_path = os.path.join(OPENAI_RESPONSE_LOG_PATH, filename)
    async with aiofiles.open(file_path, "w") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=4))


def sync_write_to_file(data: dict, filename: str):
    os.makedirs(OPENAI_RESPONSE_LOG_PATH, exist_ok=True)
    file_path = os.path.join(OPENAI_RESPONSE_LOG_PATH, filename)
    with open(file_path, "w") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))


class OpenAIChatArgs(BaseModelArgs):
    model: str = Field(default="gpt-3.5-turbo")
    max_tokens: Optional[int] = Field(default=None)
    temperature: float = Field(default=1.0)
    top_p: float = Field(default=1.0)
    n: int = Field(default=1)
    stop: Optional[Union[str, List]] = Field(default=None)
    presence_penalty: int = Field(default=0)
    frequency_penalty: int = Field(default=0)


# To support your own local LLMs, register it here and add it into LOCAL_LLMS.
@llm_registry.register("openai-chat")
@llm_registry.register("local")
class OpenAIChat(BaseChatModel):
    args: OpenAIChatArgs = Field(default_factory=OpenAIChatArgs)

    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0

    def __init__(self, max_retry: int = 3, **kwargs):
        args = OpenAIChatArgs()
        args = args.model_dump()
        for k, v in args.items():
            args[k] = kwargs.pop(k, v)
        if len(kwargs) > 0:
            logger.warn(f"Unused arguments: {kwargs}")
        if args["model"] in LOCAL_LLMS:
            openai.api_base = "http://localhost:5000/v1"
            openai.api_key = "EMPTY"
        super().__init__(args=args, max_retry=max_retry)

    @classmethod
    def send_token_limit(self, model: str) -> int:
        send_token_limit_dict = {
            "gpt-3.5-turbo": 4096,
            "gpt-35-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "llama-2-7b-chat-hf": 4096,
        }

        return send_token_limit_dict[model]

    @retry(
        stop=stop_after_attempt(20),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
        before_sleep=log_retry,
    )
    async def agenerate_response(
        self,
        prepend_prompt: str | list[str] = "",
        history: List[dict] = [],
        append_prompt: str | list[str] = "",
        tools: List[dict] | NotGiven = NOT_GIVEN,
        response_format: dict | NotGiven = NOT_GIVEN,
        **kwargs,
    ) -> LLMResult:
        if isinstance(prepend_prompt, str):
            prepend_prompt = [prepend_prompt]
        if isinstance(append_prompt, str):
            append_prompt = [append_prompt]

        messages = self.construct_messages(prepend_prompt, history, append_prompt)
        logger.log_prompt(messages)

        model_args = deepcopy(self.args.model_dump())
        model_args.update(kwargs)

        response: ChatCompletion = await async_openai_client.chat.completions.create(
            messages=messages,
            tools=tools,
            response_format=response_format,
            **model_args,
        )

        if OPENAI_RESPONSE_LOG_PATH:
            serializable_messages = []
            try:
                for message in messages:
                    if "tool_calls" in message:
                        message = deepcopy(message)
                        tool_call = []
                        for call in message["tool_calls"]:
                            tool_call.append(call.model_dump())
                        message["tool_calls"] = tool_call
                    serializable_messages.append(message)
            except Exception as e:
                logger.error(f"Failed to serialize messages: {e}")
            data_to_save = {
                "messages": serializable_messages,
                "tools": None if tools is NOT_GIVEN else tools,
                "response_format": (None if response_format is NOT_GIVEN else response_format),
                "model_args": model_args,
                "response": response.model_dump(),
            }
            filename = f"openai_response_{uuid4()}.json"
            try:
                await async_write_to_file(data_to_save, filename)
            except Exception as e:
                logger.error(f"Failed to save OpenAI response: {e}")

        if response.choices[0].finish_reason == "content_filter":
            raise ValueError("The response is filtered by OpenAI's content filter.")

        if response_format is not NOT_GIVEN and response_format["type"] == "json_object":
            if response.choices[0].message.content is not None:
                try:
                    # content = json.loads(JsonRepair(response.choices[0].message.content).repair())
                    content = json.loads(response.choices[0].message.content)
                except json.JSONDecodeError:
                    content = json.loads(JsonRepair(response.choices[0].message.content).repair())

            else:
                content = None
        else:
            content = response.choices[0].message.content
            # if content is None:
            #     raise ValueError("The returned content is None. Retrying...")

        if response.choices[0].message.tool_calls is not None:
            assert tools is not NOT_GIVEN
            if response.choices[0].message.tool_calls[0].function.name == "multi_tool_use.parallel":
                all_tool_calls = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["tool_uses"]
                response.choices[0].message.tool_calls = [
                    ChatCompletionMessageToolCall(
                        id=f"call_{uuid4()}",
                        function=Function(
                            arguments=json.dumps(call["parameters"]),
                            name=call["recipient_name"].lstrip("functions."),
                        ),
                        type="function",
                    )
                    for call in all_tool_calls
                ]
            all_tool_names = set([tool["function"]["name"] for tool in tools])

            # Validate if the generated tool calls are valid
            for tool in response.choices[0].message.tool_calls:
                tool_name = tool.function.name
                is_valid = tool_name in all_tool_names
                if not is_valid:
                    logger.warn(
                        f"The returned function name {tool_name} is not in the list of valid functions. Retrying..."
                    )
                    raise ValueError(f"The returned function name {tool_name} is not in the list of valid functions.")

        self.collect_metrics(response)
        return LLMResult(
            content=content,
            role="assistant",
            tool_calls=response.choices[0].message.tool_calls,
            send_tokens=response.usage.prompt_tokens,
            recv_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

    @retry(
        stop=stop_after_attempt(20),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
        before_sleep=log_retry,
    )
    async def generate_response(
        self,
        prepend_prompt: str | list[str] = "",
        history: List[dict] = [],
        append_prompt: str | list[str] = "",
        tools: List[dict] | NotGiven = NOT_GIVEN,
        response_format: dict | NotGiven = NOT_GIVEN,
        **kwargs,
    ) -> LLMResult:
        if isinstance(prepend_prompt, str):
            prepend_prompt = [prepend_prompt]
        if isinstance(append_prompt, str):
            append_prompt = [append_prompt]

        messages = self.construct_messages(prepend_prompt, history, append_prompt)
        logger.log_prompt(messages)

        model_args = deepcopy(self.args.model_dump())
        model_args.update(kwargs)

        response: ChatCompletion = sync_openai_client.chat.completions.create(
            messages=messages,
            tools=tools,
            response_format=response_format,
            **model_args,
        )

        if OPENAI_RESPONSE_LOG_PATH:
            serializable_messages = []
            try:
                for message in messages:
                    if "tool_calls" in message:
                        message = deepcopy(message)
                        tool_call = []
                        for call in message["tool_calls"]:
                            tool_call.append(call.model_dump())
                        message["tool_calls"] = tool_call
                    serializable_messages.append(message)
            except Exception as e:
                logger.error(f"Failed to serialize messages: {e}")
            data_to_save = {
                "messages": serializable_messages,
                "tools": None if tools is NOT_GIVEN else tools,
                "response_format": (None if response_format is NOT_GIVEN else response_format),
                "model_args": model_args,
                "response": response.model_dump(),
            }
            filename = f"openai_response_{uuid4()}.json"
            try:
                sync_write_to_file(data_to_save, filename)
            except Exception as e:
                logger.error(f"Failed to save OpenAI response: {e}")

        if response.choices[0].finish_reason == "content_filter":
            raise ValueError("The response is filtered by OpenAI's content filter.")

        if response_format is not NOT_GIVEN and response_format["type"] == "json_object":
            if response.choices[0].message.content is not None:
                try:
                    # content = json.loads(JsonRepair(response.choices[0].message.content).repair())
                    content = json.loads(response.choices[0].message.content)
                except json.JSONDecodeError:
                    content = json.loads(JsonRepair(response.choices[0].message.content).repair())

            else:
                content = None
        else:
            content = response.choices[0].message.content
            # if content is None:
            #     raise ValueError("The returned content is None. Retrying...")

        if response.choices[0].message.tool_calls is not None:
            assert tools is not NOT_GIVEN
            if response.choices[0].message.tool_calls[0].function.name == "multi_tool_use.parallel":
                all_tool_calls = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["tool_uses"]
                response.choices[0].message.tool_calls = [
                    ChatCompletionMessageToolCall(
                        id=f"call_{uuid4()}",
                        function=Function(
                            arguments=json.dumps(call["parameters"]),
                            name=call["recipient_name"].lstrip("functions."),
                        ),
                        type="function",
                    )
                    for call in all_tool_calls
                ]
            all_tool_names = set([tool["function"]["name"] for tool in tools])

            # Validate if the generated tool calls are valid
            for tool in response.choices[0].message.tool_calls:
                tool_name = tool.function.name
                is_valid = tool_name in all_tool_names
                if not is_valid:
                    logger.warn(
                        f"The returned function name {tool_name} is not in the list of valid functions. Retrying..."
                    )
                    raise ValueError(f"The returned function name {tool_name} is not in the list of valid functions.")

        self.collect_metrics(response)
        return LLMResult(
            content=content,
            role="assistant",
            tool_calls=response.choices[0].message.tool_calls,
            send_tokens=response.usage.prompt_tokens,
            recv_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

    def construct_messages(self, prepend_prompt: list[str], history: list[dict], append_prompt: list[str]):
        messages = []
        # if prepend_prompt != []:
        for i, prompt in enumerate(prepend_prompt):
            if prompt != "":
                messages.append({"role": "system" if i == 0 else "user", "content": prompt})
        if len(history) > 0:
            messages += history
        # if append_prompt != []:
        for prompt in append_prompt:
            if prompt != "":
                messages.append({"role": "user", "content": prompt})
        return messages

    def collect_metrics(self, response: ChatCompletion):
        self.total_prompt_tokens += response.usage.prompt_tokens
        self.total_completion_tokens += response.usage.completion_tokens

    def get_spend(self) -> int:
        input_cost_map = {
            "gpt-3.5-turbo": 0.0015,
            "gpt-3.5-turbo-16k": 0.003,
            "gpt-3.5-turbo-0613": 0.0015,
            "gpt-3.5-turbo-16k-0613": 0.003,
            "gpt-4": 0.03,
            "gpt-4-0613": 0.03,
            "gpt-4-32k": 0.06,
            "llama-2-7b-chat-hf": 0.0,
        }

        output_cost_map = {
            "gpt-3.5-turbo": 0.002,
            "gpt-3.5-turbo-16k": 0.004,
            "gpt-3.5-turbo-0613": 0.002,
            "gpt-3.5-turbo-16k-0613": 0.004,
            "gpt-4": 0.06,
            "gpt-4-0613": 0.06,
            "gpt-4-32k": 0.12,
            "llama-2-7b-chat-hf": 0.0,
        }

        model = self.args.model
        if model not in input_cost_map or model not in output_cost_map:
            raise ValueError(f"Model type {model} not supported")

        return (
            self.total_prompt_tokens * input_cost_map[model] / 1000.0
            + self.total_completion_tokens * output_cost_map[model] / 1000.0
        )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
)
def get_embedding(text: str) -> np.array:
    try:
        text = text.replace("\n", " ")
        if openai.api_type == "azure":
            embedding = sync_openai_client.embeddings.create(input=[text], deployment_id="text-embedding-ada-002")[
                "data"
            ][0]["embedding"]
        else:
            embedding = sync_openai_client.embeddings.create(input=[text], model="text-embedding-ada-002")["data"][0][
                "embedding"
            ]
        return tuple(embedding)
    except Exception as e:
        logger.error(f"Error {e} when requesting openai models. Retrying")
        raise
