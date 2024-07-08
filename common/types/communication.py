from pydantic import BaseModel, root_validator, Field
from typing import Any
from enum import Enum
from .llm import LLMResult
from datetime import datetime


class ContInput(BaseModel):
    sender: str
    content: str


class LaunchGoalParam(BaseModel):
    """The parameters for launching a goal.
    goal: The goal to be launched.
    team_member_names: The names of the team members. If specified, will skip the automatic teamup process.
    team_up_depth: The current depth of nested-teamup. Need not be manually specified.
    is_collaborative_planning_enabled: Whether to enable collaborative planning.
    comm_id: The communication ID. If specified, will continue the previous conversation.
    cont_info: Useful only when `comm_id` is specified. The info to continue the previous conversation."""

    goal: str
    team_member_names: list[str] | None = None
    team_up_depth: int | None = None
    is_collaborative_planning_enabled: bool = False
    comm_id: str | None = None
    cont_input: ContInput | None = None
    obs_kwargs: dict[str, Any] = {}
    max_turns: int | None = None
    skip_naming: bool = True

    @root_validator(pre=True)
    def handle(cls, values):
        cont_input = values.get("cont_input")
        comm_id = values.get("comm_id")
        if isinstance(cont_input, str):
            if cont_input == "":
                values["cont_input"] = None
            else:
                values["cont_input"] = ContInput(sender="user", content=cont_input)
        if comm_id == "":
            values["comm_id"] = None
        return values


class CommunicationProtocol(Enum):
    DISCUSSION = 0
    VOTE = 1


class CommunicationState(Enum):
    TEAMUP = 0
    DISCUSSION = 1
    VOTE = 2
    EXECUTION = 3


class CommunicationType(Enum):
    # message type
    DEFAULT = 0
    PROPOSAL = 1
    VOTE = 2
    VOTING_RESULT = 3
    DISCUSSION = 4
    SYNC_TASK_ASSIGNMENT = 5
    ASYNC_TASK_ASSIGNMENT = 6
    INFORM_TASK_RESULT = 7
    INFORM_TASK_PROGRESS = 8
    PAUSE = 9
    CONCLUDE_GROUP_DISCUSSION = 10
    CONCLUSION = 11


COMMUNICATION_TYPE_MAP = {
    "discussion": CommunicationType.DISCUSSION,
    "sync_task_assign": CommunicationType.SYNC_TASK_ASSIGNMENT,
    "async_task_assign": CommunicationType.ASYNC_TASK_ASSIGNMENT,
    "pause": CommunicationType.PAUSE,
    "conclude_group_discussion": CommunicationType.CONCLUDE_GROUP_DISCUSSION,
}


class CommunicationInfo(BaseModel):
    comm_id: str
    goal: str
    team_members: list[dict]
    memory: Any
    state: CommunicationState = CommunicationState.TEAMUP
    tool_memory: list[LLMResult] = []
    is_task_assigned: bool = False
    conclusion: str | None = None
    team_up_depth: int | None = None
    is_collaborative_planning_enabled: bool = False
    max_turns: int | None = None
    curr_turn: int = 0


class AgentMessage(BaseModel):
    content: str = ""
    sender: str = ""
    comm_id: str = ""
    next_speaker: str | list[str] = ""
    # protocol: str = ""
    state: CommunicationState = CommunicationState.TEAMUP
    type: CommunicationType = CommunicationType.DEFAULT
    proposal_id: str = ""
    # Below are for the first message after teaming up
    goal: str | None = None
    team_members: list[dict] | None = None
    team_up_depth: int | None = None
    # properties for task manager
    task_id: str = ""
    task_desc: str = ""
    # task_input: str|None=None
    task_conclusion: str = ""
    task_abstract: str = ""
    # pause+trigger
    # async task ids as triggers for PAUSE Type AgentMessage
    triggers: list[str] = []
    # Dynamic_Collaborative_Planner
    updated_plan: str = ""
    is_collaborative_planning_enabled: bool = False
    # timestamp: str = Field(default_factory=lambda: str(datetime.now()))
    max_turns: int | None = None

    def to_llm_result(self):
        return LLMResult(content=self.content, role="assistant", name=self.sender)
