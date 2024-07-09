from typing import Literal

from httpx import AsyncClient, RequestError, Timeout
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from common.config import global_config
from common.types.agent import AgentInfo
from common.types.server import AgentRegistryTeamupOutput
from common.utils.misc import log_retry


class ServerHelper:
    """
    Helper functions that help communicate with the server.
    """

    host = "http://" + global_config["server"]["hostname"]
    port = global_config["server"]["port"]
    url = f"{host}:{port}"

    @classmethod
    @retry(
        stop=stop_after_attempt(5),
        reraise=True,
        retry=retry_if_exception_type(RequestError),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=log_retry,
    )
    async def retrieve_assistant(
        cls,
        sender: str,
        capabilities: list[str],
    ) -> list[AgentInfo]:
        """
        Retrieve relevant agents from the server with specified capability keywords.
        """
        async with AsyncClient(timeout=Timeout(timeout=30)) as client:
            retrieve_result = await client.post(
                f"{cls.url}/retrieve_assistant",
                json={
                    "sender": sender,
                    "capabilities": capabilities,
                },
                timeout=60.0,
            )
            retrieve_result.raise_for_status()
            agent_infos = retrieve_result.json()
        return agent_infos

    @classmethod
    @retry(
        stop=stop_after_attempt(5),
        reraise=True,
        retry=retry_if_exception_type(RequestError),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=log_retry,
    )
    async def register(
        cls,
        name: str,
        desc: str,
        agent_type: Literal["Human Assistant", "Thing Assistant"],
    ) -> None:
        """
        Register the client to the server
        """
        async with AsyncClient(timeout=Timeout(timeout=30)) as client:
            response = await client.post(
                f"{cls.url}/register",
                json=AgentInfo(name=name, desc=desc, type=agent_type).model_dump(),
                timeout=60,
            )
            response.raise_for_status()

    @classmethod
    @retry(
        stop=stop_after_attempt(5),
        reraise=True,
        retry=retry_if_exception_type(RequestError),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=log_retry,
    )
    async def teamup(
        cls, sender: str, agent_names: list[str], team_name: str | None = None
    ) -> AgentRegistryTeamupOutput:
        """
        Forming group with specified agents
        """
        async with AsyncClient(timeout=Timeout(timeout=30)) as client:
            teamup_result = await client.post(
                f"{cls.url}/teamup",
                json={
                    "sender": sender,
                    "agent_names": agent_names,
                    "team_name": team_name,
                },
            )
            teamup_result.raise_for_status()
            team_info = AgentRegistryTeamupOutput.model_validate_json(teamup_result.text)
        return team_info

    @classmethod
    @retry(
        stop=stop_after_attempt(5),
        reraise=True,
        retry=retry_if_exception_type(RequestError),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=log_retry,
    )
    async def query_assistant(cls, name: list[str] | str):
        async with AsyncClient(timeout=Timeout(timeout=30)) as client:
            response = await client.post(
                f"{cls.url}/query_assistant",
                json={"name": name},
            )
            response.raise_for_status()
        return response.json()
