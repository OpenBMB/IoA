from typing import Literal
from pydantic import BaseModel


class AgentInfo(BaseModel):
    """Data model for agent info that is sent between server and client"""

    # id: str
    name: str
    type: Literal["Human Assistant", "Thing Assistant"]
    desc: str


class AgentEntry(BaseModel):
    """Data model for agent info that is stored in the database"""

    # id: str
    name: str
    type: Literal["Human Assistant", "Thing Assistant"]
    desc: str
    created_at: str
    # online: bool = False


class VoteMessage(BaseModel):
    """Data model for vote message"""

    voter: str
    vote: str
    reason: str
