from __future__ import annotations
from pydantic import BaseModel


class AgentRegistryRetrivalParam(BaseModel):
    sender: str
    capabilities: list[str]


class AgentRegistryTeamupParam(BaseModel):
    sender: str
    agent_names: list[str]
    team_name: str | None = None


class AgentRegistryTeamupOutput(BaseModel):
    comm_id: str
    agent_names: list[str]


class AgentRegistryQueryParam(BaseModel):
    name: str | list[str]


class ChatRecordFetchParam(BaseModel):
    comm_id: str | list[str] | None = None
