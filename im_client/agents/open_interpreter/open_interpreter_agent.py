from interpreter import interpreter
from interpreter import OpenInterpreter
import os
from pydantic import BaseModel
from fastapi import FastAPI
import uuid
import time
import litellm
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio

app = FastAPI()


class TaskDesc(BaseModel):
    task_desc: str
    model: str


class MemoryAdded(BaseModel):
    role: str
    content: str


interpreter.auto_run = True


def fixed_litellm_completions_modified(**params):
    """
    Just uses a dummy API key, since we use litellm without an API key sometimes.
    Hopefully they will fix this!
    """

    first_error = None
    retries = 0
    max_retries = 20
    while retries < max_retries:
        try:
            yield from litellm.completion(**params, max_retries=5, num_retries=5)

            break
        except Exception as e:
            retries += 1
            if retries >= max_retries:
                first_error = e
                # LiteLLM can fail if there's no API key,
                # even though some models (like local ones) don't require it.
                if "api key" in str(first_error).lower() and "api_key" not in params:
                    print(
                        "LiteLLM requires an API key. Please set a dummy API key to prevent this message. (e.g `interpreter --api_key x` or `interpreter.llm.api_key = 'x'`)"
                    )

                # So, let's try one more time with a dummy API key:
                params["api_key"] = "x"

                try:
                    yield from litellm.completion(**params)
                except:
                    # If the second attempt also fails, raise the first error
                    raise first_error

            else:
                time.sleep(3)


@app.post("/run")
async def run(task_desc: TaskDesc):
    interpreter_instance = OpenInterpreter()
    interpreter_instance.llm.completions = fixed_litellm_completions_modified
    interpreter_instance.system_message += (
        "Just run automatically without asking for user's confirmation or feedback until the task is totally completed."
    )
    interpreter_instance.messages = []
    interpreter_instance.auto_run = True
    interpreter_instance.force_task_completion = True
    interpreter_instance.llm.api_key = os.environ.get("OPENAI_API_KEY")
    interpreter_instance.llm.api_base = os.environ.get("OPENAI_BASE_URL")

    if task_desc.model != "":
        interpreter_instance.model = task_desc.model
    interpreter_instance.model = "gpt-4-1106-preview"
    print(f"interpreter model: {interpreter_instance.model}...")
    task_desc.task_desc = "Here is a task that you should finish:\n" + task_desc.task_desc
    try:
        intermediate_msgs = await safe_chat(interpreter_instance, task_desc.task_desc)
        conclusion_msgs = await safe_chat(
            interpreter_instance,
            "Please summarize and provide a complied and complete conclusion as the final answer to the previous task I assigned to you. If there are any files or codes in the final answer, please print them out.",
        )
    except Exception as e:
        return {
            "task_id": uuid.uuid4().hex,
            "conclusion": "Internal Server Error! The task is not completed!",
        }

    conclusion = [f"{item['content']}\n" for item in conclusion_msgs]
    conclusion = "".join(conclusion)
    messages = interpreter_instance.messages

    del interpreter_instance
    return {
        "task_id": uuid.uuid4().hex,
        "task_desc": task_desc,
        "steps": messages,
        "conclusion": conclusion,
    }


async def safe_chat(interpreter_instance, message):
    max_retries = 3
    retries = 0
    messages = interpreter_instance.messages

    while retries < max_retries:
        try:
            interpreter_instance.messages = messages
            response = await asyncio.to_thread(interpreter_instance.chat, message)
            return response
        except Exception as e:
            print(f"An error occurred: {e}. Retrying...")
            import traceback

            traceback.print_exc()
            await asyncio.sleep(10)
            retries += 1
    raise Exception("Failed to complete the operation after several retries.")


# TODO: update get_memory, instance of interpreter should be used.
@app.post("/get_memory")
async def get_memory():
    return interpreter.messages


# TODO: update add_to_memory, instance of interpreter should be used.
@app.post("/add_to_memory")
async def add_to_memory(memoryAdded: MemoryAdded):
    interpreter.messages.append({"role": memoryAdded.role, "type": "message", "content": memoryAdded.content})


@app.post("/keep_alive")
async def keep_alive_endpoint():
    return {"message": "Keep alive endpoint"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7070)
