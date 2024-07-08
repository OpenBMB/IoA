from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymilvus import connections

from agents import AgentAdapter
from communication.communication_layer import CommunicationLayer
from common.config import global_config
from common.types import LaunchGoalParam


@asynccontextmanager
async def lifespan(app: FastAPI):
    global communicator
    if communicator is None:
        tool_agent = AgentAdapter.create(global_config["tool_agent"])
        comm_config = global_config["comm"]
        communicator = await CommunicationLayer.create(
            comm_config["name"],
            comm_config["desc"],
            comm_config["type"],
            tool_agent,
            comm_config["support_nested_teams"],
            discussion_only=comm_config["discussion_only"],
        )
    yield
    await communicator.shutdown()


app = FastAPI(lifespan=lifespan)

communicator: CommunicationLayer = None

connections.connect(
    alias="default",
    user="username",
    password="password",
    # host='localhost', #'host.docker.internal',
    host="standalone",
    port="19530",
)


@app.post("/launch_goal")
async def launch_goal(param: LaunchGoalParam):
    return await communicator.launch_goal(**param.model_dump())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5050)
