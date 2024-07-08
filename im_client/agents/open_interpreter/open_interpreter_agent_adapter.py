from .. import AgentAdapter
from pydantic import BaseModel
import requests
from common.types.llm import LLMResult
from typing import List, Dict
from docker.models.containers import Container
from common.config import global_config
import os
import json
import aiohttp
import asyncio
import traceback


class TaskDesc(BaseModel):
    task_desc: str
    model: str


class MemoryAdded(BaseModel):
    role: str
    content: str


class MemoryGot(BaseModel):
    responses: List[Dict]


class OpenInterpreterAgent(AgentAdapter):
    def __init__(
        self,
        docker_container: Container,
        agent_name: str,
    ):
        self.docker_container = docker_container
        self.agent_name = agent_name
        self.task_desc = ""
        self.url = f"http://{global_config['tool_agent']['container_name']}:7070"

        # create log directory
        self.log_path = f"/app/tool_agent_log"

        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)

    async def run(self, task_desc: str, model: str = "gpt-4-1106-preview"):
        data = TaskDesc(task_desc=task_desc, model=model)
        headers = {"Content-Type": "application/json"}
        print(f"the model specified in Open Interpreter: {data.model}...")
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.url + "/run", json=data.model_dump(), headers=headers) as response:
                        item = await response.json()
                        conclusion = item["conclusion"]
                        break
            except Exception as e:
                print(f"error while get the conclusion from open interpreter agent...:{e}")
                traceback.print_exc()
                await asyncio.sleep(3)
                continue

        filename = f"{item['task_id']}.json"
        file_path = os.path.join(self.log_path, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(item, f, ensure_ascii=False, indent=4)
        print(f"Task completion process has been recorded successfully to {file_path}.")

        return conclusion
        # TODO: run() should have return value

    async def add_to_memory(self, memoryAdded: LLMResult):
        headers = {"Content-Type": "application/json"}
        data = MemoryAdded(role=memoryAdded.role, content=memoryAdded.content)
        requests.post(
            self.url + "/add_to_memory",
            json=data.model_dump(),
            headers=headers,
        )

    async def get_memory(self) -> list[LLMResult]:
        responses = requests.post(self.url + "/get_memory").json()
        messageList: list[LLMResult] = []
        for response in responses:
            print(response)
            llmResult = LLMResult(role=response["role"], content=response.get("content"))
            language = response.get("language", None)

            if language:
                llmResult.content += f"\n```{language}\n{response.get('code', None)}\n```"
            output = response.get("output", None)
            if output:
                llmResult.content += f"\noutput: {output}\n"
            messageList.append(llmResult)
        return messageList

    async def shutdown(self):
        await self.docker_container.remove(force=True)
