from .. import AgentAdapter
from docker.models.containers import Container
import requests
from common.config import global_config
import os
import json
import time
import aiohttp
import asyncio
import traceback


class AutoGPTAgent(AgentAdapter):
    def __init__(self, docker_container: Container, agent_name: str):
        self.docker_container = docker_container
        self.agent_name = agent_name
        self.task_desc = ""
        # Agent Protocol endpoints
        self.url = f"http://{global_config['tool_agent']['container_name']}:8000/ap/v1/agent/tasks"

        # create log directory
        self.log_path = f"/app/tool_agent_log"

        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)

    async def run(self, task_desc: str):
        headers = {"Content-Type": "application/json"}
        task_desc = (
            task_desc
            + "\nDo not ask user anything. The task must be ended with a detailed description of the solution and the actions that have been done."
        )

        task_id = await self.create_task(task_desc, headers)

        if not task_id:
            return "Failed to create the task."

        await self.complete_task(task_id, headers)

        conclusion = await self.draw_conclusion(task_id, headers)

        # save the log
        await self.save_autogpt_log(task_id, task_desc, conclusion, headers)
        return conclusion

    async def create_task(self, task_desc: str, headers: dict, max_tries: int = 8) -> str | None:
        """
        Attempt to create a task with a retry mechanism.

        This function sends an HTTP POST request to create a new task. It retries
        the request up to `max_tries` times in case of failure, waiting 5 seconds
        between attempts. If the task creation is successful, it returns the task ID
        as a string. If all retries fail, it returns None.

        Parameters:
        task_desc (str): The description of the task to be created.
        headers (dict): The headers to include in the request.
        max_tries (int, optional): The maximum number of retry attempts (default is 8).

        Returns:
        str or None: The task ID as a string if the task creation is successful; None if it fails.
        """
        retry = 1
        async with aiohttp.ClientSession() as session:
            while retry <= max_tries:
                async with session.post(
                    self.url,
                    json={
                        "input": "Here is a task that you should finish: " + task_desc,
                        "additional_input": {},
                    },
                    headers=headers,
                ) as response:
                    try:
                        task_info = await response.json()
                        task_id = task_info["task_id"]
                        return task_id
                    except Exception as e:
                        print(f"error while creating task...:{e}")
                        print(traceback.print_exc())
                        await asyncio.sleep(5)
                        retry += 1
            return None

    async def complete_task(self, task_id: str, headers: dict, max_steps: int = 20):
        """
        Execute the task steps until completion or a maximum number of steps is reached.

        This function sends repeated HTTP POST requests to execute the steps of the task.
        It continues to send requests until the task is completed or the maximum number of
        steps is reached. If the cumulative cost of the task exceeds a certain threshold,
        a different input is sent to expedite the task completion.

        Args:
            task_id (str): The ID of the task to be completed.
            headers (dict): The headers to include in the request.
            max_steps (int): The maximum number of steps to attempt (default is 20).

        Returns:
            This function does not return any value.
        """
        current_step = 1
        cost = 0

        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    if float(cost) > 1.5:
                        async with session.post(
                            self.url + "/" + str(task_id) + "/steps",
                            json={
                                "input": "You should finish the task as quickly as possible.",
                                "additional_input": {},
                            },
                            headers=headers,
                        ) as response:
                            step = await response.json()
                    else:
                        async with session.post(
                            self.url + "/" + str(task_id) + "/steps",
                            headers=headers,
                        ) as response:
                            step = await response.json()
                except Exception as e:
                    print(f"error while making one step...:{e}")
                    traceback.print_exc()
                    await asyncio.sleep(3)
                    continue

                if step:
                    if (
                        "additional_output" in step
                        and step["additional_output"]
                        and "task_cumulative_cost" in step["additional_output"]
                    ):
                        cost = step["additional_output"]["task_cumulative_cost"]
                else:
                    await asyncio.sleep(3)
                    continue
                print(str(step))

                if "is_last" in step:
                    current_step += 1
                    if current_step >= max_steps or step["is_last"]:
                        break

    async def draw_conclusion(self, task_id: str, headers: dict, max_steps: int = 20) -> str:
        """
        Retrieve the conclusion of the task.

        This function sends an HTTP POST request to retrieve the conclusion of the task.
        It continues to retrieve the task's steps until the task is completed or the maximum
        number of steps is reached.

        Args:
            task_id (str): The ID of the task.
            headers (dict): The headers to include in the request.

        Returns:
            str: The compiled conclusion of the task.
        """
        conclusion = ""
        async with aiohttp.ClientSession() as session:
            # create the task for conclusion
            while True:
                try:
                    async with session.post(
                        self.url + "/" + str(task_id) + "/steps",
                        json={
                            "input": "Now you should summarize and provide a complied and complete conclusion in text form as the final answer to the previous task I assigned to you. If there are any files in the final answer, please print them out. You should focus on compiling the information gathered and so do not use any web or code commands.",
                            "additional_input": {},
                        },
                        headers=headers,
                    ) as response:
                        step = await response.json()
                        if step:
                            print(str(step))
                            if "output" in step:
                                conclusion += str(step["output"]) + "\n"
                                break
                except Exception as e:
                    print(f"error while creating the task for conclusion...:{e}")
                    traceback.print_exc()
                    await asyncio.sleep(3)

            current_step = 1
            while True:
                if step and "is_last" in step and step["is_last"]:
                    break
                try:
                    async with session.post(
                        self.url + "/" + str(task_id) + "/steps",
                        headers=headers,
                    ) as response:
                        step = await response.json()
                        if step:
                            print(str(step))
                            if "output" in step:
                                conclusion += str(step["output"]) + "\n"
                                current_step += 1
                                if current_step >= max_steps:
                                    break
                        else:
                            await asyncio.sleep(3)
                except Exception as e:
                    print(f"error while drawing conclusion...:{e}")
                    traceback.print_exc()
                    await asyncio.sleep(3)
        return conclusion

    async def save_autogpt_log(self, task_id: str, task_desc: str, conclusion: str, headers: dict) -> str | None:
        """
        Save the task and its steps to a log file.

        This function retrieves the task and its steps and saves them to a log file in JSON format.

        Args:
            task_id (str): The ID of the task.
            task_desc (str): The description of the task.
            headers (dict): The headers to include in the request.
        Returns:
            str: The file path of the saved log.
        """
        retry = 1
        max_retries = 5
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with session.get(
                        self.url + "/" + str(task_id),
                        headers=headers,
                    ) as response:
                        task = await response.json()
                    async with session.get(
                        self.url + "/" + str(task_id) + "/steps",
                        headers=headers,
                    ) as response:
                        steps = await response.json()
                    item = {
                        "task_id": task_id,
                        "task_desc": task_desc,
                        "task": task,
                        "steps": steps,
                        "conclusion": conclusion,
                    }
                    # 文件名以 task_id 命名，保存为 .json 格式
                    filename = f"{item['task_id']}.json"
                    file_path = os.path.join(self.log_path, filename)
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(item, f, ensure_ascii=False, indent=4)
                    print(conclusion)
                    print(f"Task completion process has been recorded successfully to {file_path}.")
                    return file_path

                except Exception as e:
                    print(f"error while saving the log...:{e}")
                    traceback.print_exc()
                    await asyncio.sleep(3)
                    retry += 1
                    if retry >= max_retries:
                        return None

    async def shutdown(self):
        await self.docker_container.remove(force=True)
