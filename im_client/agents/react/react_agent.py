import os
from string import Template
from collections import defaultdict

import yaml
from fastapi import FastAPI
from pydantic import BaseModel
from tools import TOOL_MAPPING, BROWSER_TOOLS_MAPPING

from llms import OpenAIChat
from memory import ChatHistoryMemory
from prompts import (
    REACT_APPEND_THOUGHT_PROMPT,
    REACT_APPEND_TOOL_PROMPT,
    REACT_SYSTEM_PROMPT,
    REACT_TASK_PROMPT,
)
from common.log import logger
from common.types.llm import LLMResult
from common.utils.tool_utils import ToolResponse
from tools.playwright_browser import SimpleTextBrowser

app = FastAPI()


class TaskDesc(BaseModel):
    task_desc: str
    uid: str


class MemoryAdded(BaseModel):
    role: str
    message: str


SUBMIT_TOOL = {
    "type": "function",
    "function": {
        "name": "submit_task",
        "description": "Use this function at the end of the task handling process. As the user and other agents do not have access to your intermediate steps and the solution presented in your calling of `subtask_solver`, you should write the COMPLETE final answer in the `conclusion` parameter of this function. Include as many information from your exploration as possible.",
        "parameters": {
            "type": "object",
            "properties": {
                "conclusion": {
                    "description": "Use around 400 words to summarize what you have done to handle this task, especially some milestones (such as writing what content to file xxx, getting what information from web xxx). Present the final answer explicitly in details. Only this conclusion will be shown to user, so you must write down enough detailed information that summarize all the things and information you got.",
                    "type": "string",
                }
            },
            "required": ["conclusion"],
        },
    },
}

SUBTASK_TOOL = {
    "type": "function",
    "function": {
        "name": "subtask_solver",
        "description": "Define subtask and generate its response by yourself if you want to solve subtask rather than generate thought or call other tools.",
        "parameters": {
            "type": "object",
            "properties": {
                "subtask": {
                    "description": "The brief description of the subtask you want to create and solve by yourself.",
                    "type": "string",
                },
                "solution": {
                    "description": "your detailed and self-contained response to the subtask.",
                    "type": "string",
                },
            },
            "required": ["subtask", "solution"],
        },
    },
}


class ReActAgentServer:
    def __init__(
        self,
        agent_name: str,
        agent_desc: str,
        model: str,
        tools: list[dict] = [],
        max_num_steps: int = 20,
    ):
        self.agent_name = agent_name
        self.agent_desc = agent_desc
        self.tools = tools
        has_submit_tool = False
        has_subtask_tool = False
        for tool in self.tools:
            if tool["function"]["name"] == "submit_task":
                has_submit_tool = True
            if tool["function"]["name"] == "subtask_solver":
                has_subtask_tool = True
        if not has_submit_tool:
            self.tools.append(SUBMIT_TOOL)
        if not has_subtask_tool:
            self.tools.append(SUBTASK_TOOL)

        self.memory = defaultdict(lambda: ChatHistoryMemory())
        self.step_cnt = defaultdict(lambda: 0)
        self.task_desc = defaultdict(lambda: "")
        self.conclusion = defaultdict(lambda: "")
        self.cookies = defaultdict(lambda: None)
        self.llm = OpenAIChat(model=model)

        self.browser = SimpleTextBrowser(bing_api_key=os.getenv("BING_API_KEY"))

        self.max_num_steps = max_num_steps
        # self.reset()

    def reset(self, uid: str):
        self.step_cnt[uid] = 0
        self.task_desc[uid] = ""
        self.conclusion[uid] = ""
        self.cookies[uid] = None
        self.memory[uid].reset()

    async def run(self, task_desc: str, uid: str):
        await self.create_task(task_desc, uid)
        while not await self.is_finished(uid):
            await self.step(uid)
            logger.info(f"Step: {self.step_cnt[uid]} completed")
        logger.info(f"UID: {uid} - Task is finished. Conclusion: {self.conclusion[uid]}")
        if self.conclusion[uid] != "":
            return self.conclusion[uid]
        else:
            # TODO: summarize the reason on failure and the current progress
            return "Failed to handle the task."

    async def step(self, uid: str):
        # Get the latest messages from the memory
        messages = await self.memory[uid].to_messages(self.agent_name)

        # Generate the prompt
        prepend_prompt = [
            Template(REACT_SYSTEM_PROMPT).safe_substitute({"name": self.agent_name, "desc": self.agent_desc}),
            Template(REACT_TASK_PROMPT).safe_substitute({"task_description": self.task_desc[uid]}),
        ]
        # Generate the response

        response: LLMResult = await self.llm.agenerate_response(
            prepend_prompt=prepend_prompt,
            history=messages,
            append_prompt=REACT_APPEND_THOUGHT_PROMPT,
            tools=self.tools,
            response_format={"type": "json_object"},
            temperature=0.5,
        )
        if response.tool_calls != []:
            response.tool_calls = None
        if isinstance(response.content, dict):
            response.content = "Thought: " + response.content["thought"]

        # Add the response to the memory
        logger.log_llm_result(response)
        await self.add_to_memory(response, uid)

        # if response.parsed_tool_calls:
        #     for i, tool_call in enumerate(response.parsed_tool_calls):
        if self.step_cnt[uid] == self.max_num_steps:
            tool_choice = {
                "type": "function",
                "function": {"name": SUBMIT_TOOL["function"]["name"]},
            }
        else:
            tool_choice = None

        thought_messages = await self.memory[uid].to_messages(self.agent_name)

        response_tool: LLMResult = await self.llm.agenerate_response(
            prepend_prompt=prepend_prompt,
            history=thought_messages,
            append_prompt=REACT_APPEND_TOOL_PROMPT,
            tools=self.tools,
            tool_choice=tool_choice,
        )

        if isinstance(response_tool.content, dict):
            response_tool.content = "Tool: " + response_tool.content["tool"]

        # Add the response to the memory
        logger.log_llm_result(response_tool)
        await self.add_to_memory(response_tool, uid)

        if response_tool.parsed_tool_calls:
            for i, tool_call in enumerate(response_tool.parsed_tool_calls):
                tool_name = tool_call.function.name
                tool_input = tool_call.function.arguments
                tool_call_id = tool_call.id

                if tool_name == SUBMIT_TOOL["function"]["name"]:
                    self.conclusion[uid] = tool_input["conclusion"]
                    break
                elif tool_name in TOOL_MAPPING:
                    try:
                        tool_response = ToolResponse(observation=TOOL_MAPPING[tool_name](**tool_input))
                    except Exception as e:
                        tool_response = ToolResponse(observation=f"Error in calling tool {tool_name}: {e}")
                elif tool_name in BROWSER_TOOLS_MAPPING:
                    try:
                        if tool_name in ["read_page_and_answer", "summarize_page"]:
                            tool_response = ToolResponse(
                                observation=(
                                    await BROWSER_TOOLS_MAPPING[tool_name](self.browser, self.llm, **tool_input)
                                )
                            )
                        else:
                            tool_response = ToolResponse(
                                observation=await BROWSER_TOOLS_MAPPING[tool_name](self.browser, **tool_input)
                            )
                    except Exception as e:
                        tool_response = ToolResponse(observation=f"Error in calling tool {tool_name}: {e}")
                elif tool_name == SUBTASK_TOOL["function"]["name"]:
                    if "subtask" in tool_input and "solution" in tool_input:
                        tool_response: ToolResponse = ToolResponse(observation="The record of subtask_solver saved.")
                    else:
                        tool_response: ToolResponse = ToolResponse(observation="The call of subtask_solver failed.")
                else:
                    logger.warn(f"Agent generated invalid tool call:\n{tool_name}\n{tool_input}")
                    tool_response = ToolResponse(observation=f"{tool_name} could not be found.")

                tool_response_result = tool_response.to_llm_result(tool_call_id)
                logger.log_llm_result(tool_response_result)
                await self.add_to_memory(tool_response_result, uid)

        self.step_cnt[uid] += 1

    async def create_task(self, task_desc: str, uid: str):
        self.reset(uid)
        self.task_desc[uid] = task_desc

    async def add_to_memory(self, message: LLMResult | list[LLMResult], uid: str):
        if isinstance(message, list):
            message = [message]
        self.memory[uid].add_messages(message)

    async def get_memory(self, uid: str):
        return await self.memory[uid].to_messages(self.agent_name)

    async def is_finished(self, uid: str):
        return self.conclusion[uid] != "" or self.step_cnt[uid] > self.max_num_steps


tools = []
if tool_config_file := os.getenv("TOOLS_CONFIG", ""):
    tools = yaml.safe_load(open(tool_config_file))
assert os.getenv("AGENT_MODEL", "") != "", "AGENT_MODEL is not set. Pass the model for ReAct Agent in config file!"
reactagent = ReActAgentServer(
    os.getenv("AGENT_NAME", "ReAct Agent"),
    os.getenv(
        "AGENT_DESC",
        "The ReAct agent is designed as an affordable and straightforward agent. It is well-suited for handling routine tasks. However, it is important to note that it may not be able to tackle highly complex problems.",
    ),
    os.getenv("AGENT_MODEL"),
    tools,
    int(os.getenv("MAX_NUM_STEPS", 20)),
)


@app.post("/run")
async def run(task_desc: TaskDesc):
    return await reactagent.run(task_desc.task_desc, task_desc.uid)


@app.post("/keep_alive")
async def keep_alive_endpoint():
    return {"message": "Keep alive endpoint"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7070)
