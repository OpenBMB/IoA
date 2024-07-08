import asyncio
import json
import os
import random
import re
import urllib
from copy import deepcopy
from string import Template
from typing import Any, Literal, Tuple

import yaml
from agents.base import AgentAdapter
from llms import load_llm
from memory import ChatHistoryMemory
from observation_func import observation_registry
from openai.types.chat import ChatCompletionMessageToolCall
from prompts import (
    COMM_APPEND_PROMPT,
    COMM_CONCLUDE_APPEND_PROMPT,
    COMM_COORDINATION_WITHOUT_GOAL_PROMPT,
    COMM_DISCOVERY_PROMPT,
    COMM_DISCUSSION_ONLY_DISCUSSION_APPEND_PROMPT,
    COMM_DISCUSSION_WITH_PLAN_APPEND_PROMPT,
    COMM_DISCUSSION_WITHOUT_PLAN_APPEND_PROMPT,
    COMM_HUMANAGENT_SYSTEM_PROMPT,
    COMM_INFORM_OPT_EXE_APPEND_PROMPT,
    COMM_MAS_PROMPT,
    COMM_PAUSE_APPEND_PROMPT,
    COMM_PAUSE_SYS_PROMPT,
    COMM_PLANNER_PROMPT,
    COMM_TASK_MANAGEMENT_APPEND_PROMPT,
    COMM_THINGAGENT_SYSTEM_PROMPT,
    COMM_UPDATE_PLAN_APPEND_PROMPT,
    COMM_WHETHER_TEAM_UP_PROMPT,
    EXEC_TASK_CONCLUSION_APPEND_PROMPT,
    REPHRASE_TASK_APPEND_PROMPT,
    REPHRASE_TASK_HYBIRD_SYS_PROMPT,
    TEAMUP_GROUP_NAMING_PROMPT,
)
from server_helper import ServerHelper

from common.config import global_config
from common.log import logger
from common.types import CommunicationInfo, CommunicationState, CommunicationType
from common.types.communication import AgentMessage, COMMUNICATION_TYPE_MAP
from common.types.llm import LLMResult
from common.utils.database_utils import AutoStoredDict
from common.utils.milvus_utils import ConfigMilvusWrapper

from .task_management import TaskEntry, TaskManager, TaskStatus
from .websocket_client import WebSocketClient

TEAM_UP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "agent_discovery",
            "description": "Discover new agents in the network by searching with natural langugae queries which could be desired expertises, skills, agent description, tasks suitable and so on.",
            "parameters": {
                "type": "object",
                "properties": {
                    "queries": {
                        "description": "List of natural langugae queries, which could be desired expertises, skills, agent description, tasks suitable and so on.",
                        "type": "array",
                        "items": {"type": "string"},
                    }
                },
                "required": ["queries"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "team_up",
            "description": "Initiate a group chat session aimed at facilitating collaboration among a team of agents identified by their unique agent names.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_members": {
                        "description": "An array of unique strings, each representing the name of an agent in the team (the name of yourself should be included).",
                        "type": "array",
                        "items": {"type": "string"},
                    }
                },
                "required": ["team_members"],
            },
        },
    },
]


def CommunicationInfo_from_dict_hook(obj: Any, **kwargs):
    instance = CommunicationInfo.model_validate(obj=obj, **kwargs)
    if instance.memory is not None:
        memory = ChatHistoryMemory.model_validate(instance.memory)
        instance.memory = memory
    return instance


class CommunicationLayer:
    """
    A class that manages communication and collaboration between agents in the Internet of Agents framework.

    This class serves as the core component for agent interaction, handling tasks such as team formation,
    message routing, task allocation, and conversation flow control.

    Attributes:
        name (str): The name of the agent.
        desc (str): A description of the agent's capabilities.
        agent_type (str): The type of agent ("Human Assistant" or "Thing Assistant").
        tool_agent (AgentAdapter): An optional third-party agent for executing specific tasks.
        server_websocket (WebSocketClient): A WebSocket client for server communication.
        support_nested_teams (bool): Whether the agent supports forming nested teams.
        discussion_only (bool): Whether the agent is limited to discussion-only mode.

    Methods:
        create: Asynchronously creates and initializes a CommunicationLayer instance.
        launch_goal: Given a goal, the client would form team with other agents to solve.
        team_up: Forms a team of agents for a specific task.
        coordination: Manages the ongoing conversation and task execution.
        shutdown: Gracefully shuts down the communication layer and associated resources.
    """

    def __init__(
        self,
        name: str,
        desc: str,
        agent_type: Literal["Human Assistant", "Thing Assistant"],
        server_websocket: WebSocketClient,
        tool_agent: AgentAdapter | None = None,
        support_nested_teams: bool = False,
        discussion_only: bool = False,
    ):
        self.name = name
        self.desc = desc
        self.agent_type = agent_type
        self.tool_agent = tool_agent
        self.server_websocket = server_websocket
        self.observation_func = observation_registry[global_config["comm"].get("observation_func", "dummy")]
        self.discussion_only = discussion_only
        self.llm = load_llm(deepcopy(global_config["comm"]["llm"]))

        if self.agent_type == "Human Assistant":
            self.system_prompt_template = COMM_HUMANAGENT_SYSTEM_PROMPT
        else:
            self.system_prompt_template = COMM_THINGAGENT_SYSTEM_PROMPT

        agent_db_name = "agent_" + re.sub(r"[^a-zA-Z0-9_]", "_", self.name)
        self.agent_contact = ConfigMilvusWrapper(
            os.path.join("configs", "vecdb", "agent_contact.yaml"),
            name_modify=agent_db_name,
        )

        self.comm_bank = AutoStoredDict(
            f"./database/{agent_db_name}/comm.db",
            tablename="comm_bank",
            object_type=CommunicationInfo,
            from_dict_hook=CommunicationInfo_from_dict_hook,
        )

        self.task_manager_bank = AutoStoredDict(
            f"./database/{agent_db_name}/comm.db",
            tablename="task_manager_bank",
            object_type=TaskManager,
        )
        self.support_nested_teams: bool = support_nested_teams  # whether the agent can organize teams (in a hierarchical structure) when assigned a task

    @classmethod
    async def create(
        cls,
        name: str,
        desc: str,
        agent_type: Literal["Human Assistant", "Thing Assistant"],
        tool_agent: AgentAdapter | None = None,
        support_nested_teams: bool = False,
        discussion_only: bool = False,
    ):
        await cls.register(name, desc, agent_type)
        server_websocket = await cls.register_websocket(name)
        layer = cls(
            name,
            desc,
            agent_type,
            server_websocket,
            tool_agent,
            support_nested_teams,
            discussion_only,
        )
        asyncio.get_event_loop().create_task(layer._listen_message())
        return layer

    @classmethod
    async def register(
        cls,
        name: str,
        desc: str,
        agent_type: Literal["Human Assistant", "Thing Assistant"],
    ):
        await ServerHelper.register(name, desc, agent_type)

    @classmethod
    async def register_websocket(cls, name: str):
        hostname = global_config["server"]["hostname"]
        port = global_config["server"]["port"]
        uri = f"ws://{hostname}:{port}/ws/{name}"
        # encode the uri
        uri = urllib.parse.quote(uri, safe=":/?&=,.")
        websocket = WebSocketClient(uri)
        await websocket.connect()
        return websocket

    async def launch_goal(
        self,
        goal: str,
        team_member_names: list[str] | None = None,
        team_up_depth: int | None = None,
        is_collaborative_planning_enabled: bool = False,
        comm_id: str | None = None,
        cont_input: dict | None = None,
        obs_kwargs: dict = {},
        max_turns: int | None = None,
        skip_naming: bool = True,
    ) -> Tuple[str, str]:
        """
        Launch a group chat targetted on the given goal.

        Args:
            goal (str): The high-level goal that this group chat aims to achieve.
            team_member_names (list[str], optional): The names of the teammates. If specified,
                then the assistant will directly team up with these teammates. Defaults to None.
            team_up_depth (int, optional): The depth of the nested team-up. Defaults to None.
            is_collaborative_planning_enabled (bool, optional): Whether the collaborative planning is enabled. Defaults to False.
            comm_id (str, optional): The id of the previous chat session. Defaults to None.
            cont_input (dict, optional): The input of the continuation message, with `content` and `sender` keys. Defaults to None.
            obs_kwargs (dict, optional): The observation arguments. Defaults to {}.
            max_turns (int, optional): The maximum turns of the chat session. Defaults to None.
            skip_naming (bool, optional): Whether to skip the naming of the team. Defaults to True.
        Returns:
            Tuple[str, str]: The id of the chat session and the conclusion of the chat session.
        """
        new_message = None
        if comm_id is None:
            # team up: determine the team members, return the comm id.
            cont_input = None
            comm_id = await self.team_up(
                goal,
                team_member_names,
                team_up_depth=team_up_depth,
                is_collaborative_planning_enabled=is_collaborative_planning_enabled,
                obs_kwargs=obs_kwargs,
                max_turns=max_turns,
                skip_naming=skip_naming,
            )
        else:
            # continue the previous discussion
            if comm_id not in self.comm_bank:
                return comm_id, f"Could not find the communication session: {comm_id}."
            comm_info: CommunicationInfo = self.comm_bank[comm_id]
            comm_info.conclusion = None
            comm_info.max_turns = max_turns
            self.comm_bank[comm_id] = comm_info
            if cont_input is not None:
                # if the continuation message is provided, then send the message to all the team members.
                # and randomly assign the next speaker.
                new_message = AgentMessage(
                    content=cont_input["content"],
                    sender=cont_input["sender"],
                    comm_id=comm_id,
                    next_speaker=random.choice([t["name"] for t in comm_info.team_members]),
                    state=CommunicationState.DISCUSSION,
                    type=CommunicationType.DISCUSSION,
                    goal=comm_info.goal,
                    team_members=comm_info.team_members,
                    team_up_depth=comm_info.team_up_depth,
                    is_collaborative_planning_enabled=comm_info.is_collaborative_planning_enabled,
                )
                self.comm_bank[comm_id] = comm_info
                await self._send_message(new_message)

        if cont_input is None:
            await self.coordination(
                new_message=new_message,
                comm_id=comm_id,
                obs_kwargs=obs_kwargs,
                max_turns=max_turns,
            )

        # check the conclusion field in polling
        while True:
            conclusion = self.comm_bank[comm_id].conclusion
            if conclusion is None:
                await asyncio.sleep(5)
            else:
                return comm_id, conclusion

    async def _naming_team(self, goal: str, team_members: list[str] = []) -> str:
        prepend_prompt = [
            Template(TEAMUP_GROUP_NAMING_PROMPT).safe_substitute(
                {"goal": goal, "teammates": json.dumps(team_members, indent=2)}
            )
        ]
        response: LLMResult = await self.llm.agenerate_response(
            prepend_prompt=prepend_prompt,
            response_format={"type": "json_object"},
        )
        try:
            team_name = response.content["team_name"]
        except:
            team_name = None
        return team_name

    async def _call_teamup_tool(
        self,
        tool_call: ChatCompletionMessageToolCall,
        goal: str,
        skip_naming: bool = True,
    ) -> Tuple[bool, LLMResult, str, list[str]]:
        tool_name = tool_call.function.name
        tool_input = tool_call.function.arguments
        tool_call_id = tool_call.id
        match tool_name:
            case "agent_discovery":
                try:
                    agent_infos = await ServerHelper.retrieve_assistant(self.name, tool_input["queries"])
                    # deduplicate agent_infos compared with self.agent_contact
                    new_agents_retrieved = []
                    for agent in agent_infos:
                        if agent.get("name") != self.name and agent.get("name") not in self.agent_contact:
                            new_agents_retrieved.append(agent)

                except Exception as e:
                    logger.error(e)
                    return False, None, None, None
                result = LLMResult(
                    content=(
                        json.dumps(new_agents_retrieved, indent=2)
                        if new_agents_retrieved
                        else "No more new agents retrieved."
                    ),
                    tool_call_id=tool_call_id,
                    name=tool_name,
                    role="tool",
                )
                logger.log_llm_result(result)
                # TODO: update the contact list.
                for agent in agent_infos:
                    if agent["name"] not in self.agent_contact and agent["name"] != self.name:
                        self.agent_contact[agent["name"]] = agent
                return False, result, None, None
            case "team_up":
                try:
                    team_member_names = tool_input["team_members"]
                    team_members = await ServerHelper.query_assistant(team_member_names)
                    team_name = None
                    if not skip_naming:
                        team_name = await self._naming_team(goal, team_members)

                    team_info = await ServerHelper.teamup(
                        sender=self.name,
                        agent_names=[agent_name for agent_name in team_member_names if agent_name != self.name],
                        team_name=team_name,
                    )

                    result = LLMResult(
                        content="Group Established.",
                        tool_call_id=tool_call_id,
                        name=tool_name,
                        role="tool",
                    )
                    logger.log_llm_result(result)
                    return True, result, team_info.comm_id, team_members
                except Exception as e:
                    logger.error(e)
                    result = LLMResult(
                        content="Group Establishment Failed.",
                        tool_call_id=tool_call_id,
                        name=tool_name,
                        role="tool",
                    )
                    logger.log_llm_result(result)
                    return False, result, None, None

    async def _discover_and_teamup(
        self,
        goal: str,
        local_contact: list[dict] | list,
        memory: ChatHistoryMemory,
        obs_kwargs: dict = {},
        skip_naming: bool = True,
        is_last_attempt: bool = False,
    ) -> Tuple[bool, str, list[str]]:
        """
        Let the agent decide whether to search for more relevent agents on the server or to team up.
        """
        observation = self.observation_func(**obs_kwargs)
        prepend_prompt = [
            Template(self.system_prompt_template).safe_substitute(
                {
                    "name": self.name,
                    "desc": self.desc,
                    "agent_type": self.agent_type,
                }
            ),
            COMM_MAS_PROMPT,
            Template(COMM_DISCOVERY_PROMPT).safe_substitute(
                {
                    "goal": goal,
                    "retrieved_contact": str(local_contact),  # TODO (vec) database -> DONE
                }
            ),
        ]
        if observation != "":
            prepend_prompt.append(f"Current Observation:\n{observation}")

        response: LLMResult = await self.llm.agenerate_response(
            prepend_prompt=prepend_prompt,
            history=(await memory.to_messages()),
            append_prompt=Template(COMM_APPEND_PROMPT).safe_substitute({"name": self.name}),
            tools=TEAM_UP_TOOLS,
            tool_choice={"type": "function", "function": {"name": "team_up"}} if is_last_attempt else "auto",
        )

        response.content = str(response.content)

        logger.log_llm_result(response)
        memory.add_messages(response)

        finished = False
        comm_id = None
        team_members = None
        if response.parsed_tool_calls:
            for i, tool_call in enumerate(response.parsed_tool_calls):
                finished, tool_response, comm_id, team_members = await self._call_teamup_tool(
                    tool_call, goal, skip_naming
                )
                if tool_response is not None:
                    memory.add_messages(tool_response)
                if finished:
                    break
        return finished, comm_id, team_members

    async def team_up(
        self,
        goal: str,
        team_member_names: list[str] | None = None,
        team_up_depth: int | None = None,
        is_collaborative_planning_enabled: bool = False,
        obs_kwargs: dict[str, Any] = {},
        max_turns: int | None = None,
        skip_naming: bool = True,
    ) -> str:
        """Given a high-level goal, the communication agent decides whether to team up
        with other agents. The server will build a chat session including all the
        teammates, and return a communication id for completing this task.

        Args:
            goal (str): The high-level goal that the user wants to achieve.
            team_member_names (list[str], optional): The names of the teammates. If specified,
                then the agent will directly team up with these teammates. Defaults to None.
        Returns:
            comm_id (str): The id of the chat session.
        """
        if team_member_names is not None:
            # if the team members have been specified
            # difrectly create a group chat for them
            agents_upated_for_contact = await ServerHelper.query_assistant(team_member_names)
            team_members = []
            for item in agents_upated_for_contact:
                if isinstance(item, dict) and item.get("name") != self.name:
                    if item.get("name" not in self.agent_contact):
                        self.agent_contact[item.get("name")] = item
                    team_members.append(item)

            team_name = None
            if not skip_naming:
                team_name = await self._naming_team(goal, team_members)

            team_info = await ServerHelper.teamup(
                sender=self.name,
                agent_names=[name for name in team_member_names if name != self.name],
                team_name=team_name,
            )
            team_members.append({"name": self.name, "type": self.agent_type, "desc": self.desc})
            comm_id = team_info.comm_id
        else:
            # if the team members are not specified, let the agent itself
            # search for the agents on the server, and decide who to teamup with
            memory = ChatHistoryMemory()
            comm_id = None
            local_contact = self.agent_contact.items()
            for i in range(global_config["comm"]["max_team_up_attempts"]):
                is_last_attempt = i == global_config["comm"]["max_team_up_attempts"] - 1
                finished, comm_id, team_members = await self._discover_and_teamup(
                    goal, local_contact, memory, obs_kwargs, skip_naming, is_last_attempt=is_last_attempt
                )

                if finished:
                    break

        if comm_id is None:
            raise ValueError("Failed to decide the teammates.")

        self.comm_bank[comm_id] = CommunicationInfo(
            comm_id=comm_id,
            goal=goal,
            team_members=team_members,
            memory=ChatHistoryMemory(),
            team_up_depth=team_up_depth,
            is_collaborative_planning_enabled=is_collaborative_planning_enabled,
            max_turns=max_turns,
        )
        self.task_manager_bank[comm_id] = TaskManager(comm_id)

        return comm_id

    def _update_memory_and_task_manager(self, new_message: AgentMessage, comm_id: str):
        """
        Update chat history and task manager
        """
        comm_info = self.comm_bank[comm_id]
        task_manager = self.task_manager_bank[comm_id]
        msg_in_memory = new_message.to_llm_result()

        comm_info.memory.add_messages(msg_in_memory)
        self.comm_bank[comm_id] = comm_info

        if new_message.type == CommunicationType.INFORM_TASK_PROGRESS:
            task_manager.update_task_manager(
                task_id=new_message.task_id,
                task_desc=new_message.task_desc,
                task_abstract=new_message.task_abstract,
                assignee=new_message.sender,
                status=TaskStatus.IN_PROGRESS,
            )
        elif new_message.type == CommunicationType.INFORM_TASK_RESULT:
            task_manager.update_task_manager(
                task_id=new_message.task_id,
                task_desc=new_message.task_desc,
                task_abstract=new_message.task_abstract,
                assignee=new_message.sender,
                status=TaskStatus.COMPLETED,
                conclusion=new_message.task_conclusion,
                msg_in_memory=msg_in_memory,
            )
            if task_manager.is_triggered():
                # the triggers in task manager are marked by True all at this point.
                if task_manager.trigger_setter == self.name:
                    new_message.next_speaker = self.name
                task_manager.clear_triggers()
        elif new_message.type == CommunicationType.PAUSE:
            task_manager.update_triggers(
                task_identifiers=new_message.triggers,
                trigger_setter=new_message.sender,
            )
        elif new_message.type == CommunicationType.CONCLUSION:
            # conclusion should be recorded
            comm_info.conclusion = new_message.content
            comm_info.curr_turn = 0
            self.comm_bank[comm_id] = comm_info
        if new_message.type in [
            CommunicationType.DISCUSSION,
            CommunicationType.ASYNC_TASK_ASSIGNMENT,
            CommunicationType.SYNC_TASK_ASSIGNMENT,
            CommunicationType.PAUSE,
            CommunicationType.CONCLUDE_GROUP_DISCUSSION,
        ]:
            if new_message.updated_plan:
                task_manager.update_plan(new_message.updated_plan)

        self.comm_bank[comm_id] = comm_info
        self.task_manager_bank[comm_id] = task_manager

    async def coordination(
        self, new_message: AgentMessage | None, comm_id: str, obs_kwargs: dict = {}, max_turns: int | None = None
    ):
        """
        Manages the coordination of agents within a group chat, handling incoming messages and directing the conversation flow.

        Args:
            new_message (AgentMessage | None): The incoming message to be processed. If None, it indicates
                the start of a new conversation where this agent is the first speaker.
            comm_id (str): The unique identifier for the current communication session or group chat.
            obs_kwargs (dict, optional): Additional keyword arguments for observation functions. Defaults to {}.
            max_turns (int | None, optional): The maximum number of conversation turns allowed. Defaults to None.

        The method performs the following key functions:
        1. Initializes or retrieves the current communication session information.
        2. Updates the communication history and task management state based on the incoming message.
        3. Determines the next action based on the message type (e.g., discussion, task assignment, conclusion).
        4. Generates and sends appropriate responses or initiates task executions.
        5. Manages the conversation flow, including state transitions and speaker selection.
        """
        if new_message and new_message.state != CommunicationState.DISCUSSION:
            logger.error("Receiving a message with a state that is not DISCUSSION.")
            return
        if comm_id not in self.comm_bank:
            self.comm_bank[comm_id] = CommunicationInfo(
                comm_id=comm_id,
                goal=new_message.goal,
                team_members=new_message.team_members,
                memory=ChatHistoryMemory(),  # TODO: configurable
                state=new_message.state,
                team_up_depth=new_message.team_up_depth,
                is_collaborative_planning_enabled=new_message.is_collaborative_planning_enabled,
                max_turns=max_turns,
            )
            self.task_manager_bank[comm_id] = TaskManager(comm_id)

        if new_message is None:
            # This agent is the first speaker.
            return await self._coordination_discussion(new_message, comm_id, obs_kwargs)
        else:
            new_message.content = f"[{new_message.sender}]: {new_message.content}"
            if new_message.sender != self.name:
                self._update_memory_and_task_manager(new_message, comm_id)
            if isinstance(new_message.next_speaker, str):
                if new_message.next_speaker != self.name:
                    return
            elif isinstance(new_message.next_speaker, list):
                if self.name not in new_message.next_speaker:
                    return

            return await self._coordination_discussion(new_message, comm_id)

    def _get_discussion_prompt(self, comm_id: str, obs_kwargs: dict = {}):
        comm_info = self.comm_bank[comm_id]
        task_manager = self.task_manager_bank[comm_id]
        observation = self.observation_func(**obs_kwargs)
        prepend_prompt = [
            Template(self.system_prompt_template).safe_substitute(
                {
                    "name": self.name,
                    "desc": self.desc,
                    "agent_type": self.agent_type,
                    "agent_name": getattr(self.tool_agent, "agent_name", ""),
                    "agent_desc": getattr(self.tool_agent, "agent_desc", ""),
                }
            ),
            COMM_MAS_PROMPT,
            Template(COMM_COORDINATION_WITHOUT_GOAL_PROMPT).safe_substitute(
                {
                    "teammates": json.dumps(
                        [t for t in comm_info.team_members if t["name"] != self.name],
                        indent=2,
                    )
                }
            ),
        ]
        if self.discussion_only:
            collaborative_management_msgs = [
                {
                    "role": "system",
                    "content": Template(COMM_TASK_MANAGEMENT_APPEND_PROMPT).safe_substitute(
                        {
                            "task_management_view": task_manager.tasks_view(),
                            "goal": comm_info.goal,
                        }
                    ),
                }
            ]

            append_prompt = [
                Template(COMM_DISCUSSION_ONLY_DISCUSSION_APPEND_PROMPT).safe_substitute({"name": self.name})
            ]
        elif comm_info.is_collaborative_planning_enabled:
            collaborative_management_msgs = [
                {
                    "role": "system",
                    "content": Template(COMM_TASK_MANAGEMENT_APPEND_PROMPT).safe_substitute(
                        {
                            "task_management_view": task_manager.tasks_view(),
                            "goal": comm_info.goal,
                        }
                    ),
                },
                {
                    "role": "system",
                    "content": Template(COMM_PLANNER_PROMPT).safe_substitute(
                        {
                            "Dynamic_Collaborative_Planner": task_manager.get_latest_plan(),
                        }
                    ),
                },
            ]
            append_prompt = [
                Template(COMM_DISCUSSION_WITH_PLAN_APPEND_PROMPT).safe_substitute(
                    {"name": self.name},
                )
            ]
        else:
            collaborative_management_msgs = [
                {
                    "role": "system",
                    "content": Template(COMM_TASK_MANAGEMENT_APPEND_PROMPT).safe_substitute(
                        {
                            "task_management_view": task_manager.tasks_view(),
                            "goal": comm_info.goal,
                        }
                    ),
                }
            ]

            append_prompt = [Template(COMM_DISCUSSION_WITHOUT_PLAN_APPEND_PROMPT).safe_substitute({"name": self.name})]

        if observation != "":
            append_prompt.append(f"Current Observation:\n{observation}")
        return prepend_prompt, collaborative_management_msgs, append_prompt

    def _get_pause_prompt(self, comm_id: str):
        comm_info = self.comm_bank[comm_id]
        task_manager = self.task_manager_bank[comm_id]

        sys_append_messages = [
            {
                "role": "system",
                "content": Template(COMM_TASK_MANAGEMENT_APPEND_PROMPT).safe_substitute(
                    {
                        "task_management_view": task_manager.tasks_view(),
                        "goal": comm_info.goal,
                    }
                ),
            },
            {
                "role": "system",
                "content": Template(COMM_PAUSE_SYS_PROMPT).safe_substitute(
                    {
                        "indices_In_Progress": task_manager.indices_filter_by_status(
                            status=[TaskStatus.TO_START, TaskStatus.IN_PROGRESS]
                        )
                    }
                ),
            },
        ]
        append_prompt = [Template(COMM_PAUSE_APPEND_PROMPT).safe_substitute({"name": self.name})]
        return sys_append_messages, append_prompt

    async def _handle_generated_pause_message(
        self,
        comm_id: str,
        parsed_response: dict,
        updated_plan: str,
        max_turns: int | None,
        obs_kwargs: dict = {},
    ):
        """
        If the generated response is a pause message, then handle the pause message.
        Prompt the model to generate the trigger, and set the trigger to the task_manager properly.
        """
        comm_info = self.comm_bank[comm_id]

        prepend_prompt, collaborative_management_msgs, append_prompt = self._get_discussion_prompt(comm_id, obs_kwargs)
        pause_messages, append_prompt = self._get_pause_prompt(comm_id)

        pause_response: LLMResult = await self.llm.agenerate_response(
            prepend_prompt=prepend_prompt,
            history=(await comm_info.memory.to_messages()) + pause_messages,
            append_prompt=append_prompt,
            response_format={"type": "json_object"},
        )
        pause_parsed_response = pause_response.content
        comm_info = self.comm_bank[comm_id]

        print("======= pause&trigger =======")
        print(pause_parsed_response)

        task_manager = self.task_manager_bank[comm_id]
        selected_task_indices = pause_parsed_response["selected_task_indices"]
        trigger_set, selected_task_ids = task_manager.set_triggers(selected_task_indices, self.name)
        self.task_manager_bank[comm_id] = task_manager
        message_to_send = AgentMessage(
            content=parsed_response["content"],
            sender=self.name,
            comm_id=comm_id,
            next_speaker="" if trigger_set else [self.name],
            state=CommunicationState.DISCUSSION,
            type=CommunicationType.PAUSE if trigger_set else CommunicationType.DISCUSSION,
            goal=comm_info.goal,
            team_members=comm_info.team_members,
            team_up_depth=comm_info.team_up_depth,
            triggers=selected_task_ids if trigger_set else [],
            updated_plan=updated_plan,
            is_collaborative_planning_enabled=comm_info.is_collaborative_planning_enabled,
            max_turns=max_turns,
        )

        await self._send_message(message_to_send)

    async def _generate_response(self, comm_id: str, obs_kwargs: dict = {}):
        comm_info = self.comm_bank[comm_id]

        prepend_prompt, collaborative_management_msgs, append_prompt = self._get_discussion_prompt(comm_id, obs_kwargs)

        max_turns = comm_info.max_turns
        curr_turn = len(await comm_info.memory.to_messages())
        if max_turns is not None and curr_turn >= max_turns:
            append_prompt.append(
                "The discussion has reached the maximum turns. Now you must send a message with type `conclude_group_discussion` anyway."
            )

        response: LLMResult = await self.llm.agenerate_response(
            prepend_prompt=prepend_prompt,
            history=(await comm_info.memory.to_messages()) + collaborative_management_msgs,
            append_prompt=append_prompt,
            response_format={"type": "json_object"},
        )

        parsed_response = response.content

        print("======= turn to speak =======")
        print(parsed_response["thought"])
        print(f"message type: {parsed_response['message_type']}")
        print(f"next_speakers: {str(parsed_response['next_people'])}")
        print(parsed_response)
        if comm_info.is_collaborative_planning_enabled:
            print(f"thought: {parsed_response['thought_on_Dynamic_Collaborative_Planner']}")
            print(
                f"update_Dynamic_Collaborative_Planner: {str(parsed_response['update_Dynamic_Collaborative_Planner'])}"
            )
        result = LLMResult(
            content=f"[{self.name}]: {parsed_response['content']}",
            name=self.name,
            role="assistant",
        )
        logger.log_llm_result(result)
        comm_info = self.comm_bank[comm_id]
        comm_info.memory.add_messages(result)
        self.comm_bank[comm_id] = comm_info

        message_type = COMMUNICATION_TYPE_MAP[parsed_response["message_type"]]

        if message_type == CommunicationType.CONCLUDE_GROUP_DISCUSSION:
            next_speakers = [self.name]
        else:
            next_speakers = (
                parsed_response["next_people"]
                if isinstance(parsed_response["next_people"], list)
                else [parsed_response["next_people"]]
            )
            team_members = {member["name"] for member in comm_info.team_members}
            next_speakers = [name for name in next_speakers if name in team_members]
            if len(next_speakers) == 0:
                next_speakers = [self.name]

        # chekc whether to update plan
        if comm_info.is_collaborative_planning_enabled:
            is_update_plan: bool = parsed_response["update_Dynamic_Collaborative_Planner"]
        else:
            is_update_plan: bool = False
        if is_update_plan:
            self.comm_bank[comm_id] = comm_info
            updated_plan = await self.update_global_plan(comm_id)
            task_manager = self.task_manager_bank[comm_id]
            task_manager.update_plan(updated_plan)
            self.task_manager_bank[comm_id] = task_manager
        else:
            updated_plan = ""

        if message_type == CommunicationType.PAUSE:
            await self._handle_generated_pause_message(comm_id, parsed_response, updated_plan, max_turns, obs_kwargs)
        else:
            # Mesage type is not pause
            message_to_send = AgentMessage(
                content=parsed_response["content"],
                sender=self.name,
                comm_id=comm_id,
                next_speaker=next_speakers,
                state=CommunicationState.DISCUSSION,
                type=message_type,
                goal=comm_info.goal,
                team_members=comm_info.team_members,
                team_up_depth=comm_info.team_up_depth,
                updated_plan=updated_plan,
                is_collaborative_planning_enabled=comm_info.is_collaborative_planning_enabled,
                max_turns=max_turns,
            )
            if message_type in [
                CommunicationType.ASYNC_TASK_ASSIGNMENT,
                CommunicationType.SYNC_TASK_ASSIGNMENT,
            ]:
                task_manager = self.task_manager_bank[comm_id]
                task_assign_manager = task_manager.task_assign_manager
                task_assign_manager.register_await_agents(next_speakers)
                self.task_manager_bank[comm_id] = task_manager
            await self._send_message(message_to_send)

    async def _handle_info_message(self, new_message: AgentMessage, comm_id: str, obs_kwargs: dict = {}):
        """
        Handle the incoming info messages, i.e., messages with type `INFORM_TASK_PROGRESS`, `INFORM_TASK_RESULT`, or `DISCUSSION`.
        """
        task_manager = self.task_manager_bank[comm_id]
        task_assign_manager = task_manager.task_assign_manager

        if new_message and (
            new_message.type
            in [
                CommunicationType.INFORM_TASK_PROGRESS,
                CommunicationType.INFORM_TASK_RESULT,
            ]
        ):
            task_assign_manager.update_await_agents(new_message.sender)
            if not task_assign_manager.check_empty():
                logger.info(f"Still awaiting: {task_assign_manager.await_agents}")
                self.task_manager_bank[comm_id] = task_manager
                return
            logger.info("Task assign manager is empty.")

        self.task_manager_bank[comm_id] = task_manager
        await self._generate_response(comm_id, obs_kwargs)

    async def _handle_async_task_assignment(self, new_message: AgentMessage, comm_id: str, obs_kwargs: dict = {}):
        """
        Handle the incoming async task assignment message. The agent will inform the tool agent to execute the task.
        And a confirmation message will be immediately sent to other agents. The discussion will be continued.
        The next speaker is the task assigner.
        """
        comm_info: CommunicationInfo = self.comm_bank[comm_id]
        observation = self.observation_func(**obs_kwargs)
        (
            reference,
            task_desc,
            task_abstract,
            context_information,
            completion_criteria,
        ) = await self._rephrase_task_to_tool_agent(comm_id, observation)
        task_manager: TaskManager = self.task_manager_bank[comm_id]
        task_id = task_manager.create_task(task_desc, task_abstract, self.name, status=TaskStatus.TO_START)
        self.comm_bank[comm_id] = comm_info
        self.task_manager_bank[comm_id] = task_manager
        asyncio.get_event_loop().create_task(
            self._call_tool_agent_and_inform(
                reference,
                task_desc,
                next_speaker="",
                comm_id=comm_id,
                task_id=task_id,
                task_abstract=task_abstract,
                context_information=context_information,
                completion_criteria=completion_criteria,
            )
        )

        parsed_response = {
            "content": Template(COMM_INFORM_OPT_EXE_APPEND_PROMPT).safe_substitute({"task_description": task_desc}),
            "next_speaker": new_message.sender,
        }
        message_to_send = AgentMessage(
            content=parsed_response["content"],
            sender=self.name,
            comm_id=comm_id,
            next_speaker=parsed_response["next_speaker"],
            state=CommunicationState.DISCUSSION,
            type=CommunicationType.INFORM_TASK_PROGRESS,
            goal=comm_info.goal,
            team_up_depth=comm_info.team_up_depth,
            team_members=comm_info.team_members,
            task_id=task_id,
            task_desc=task_desc,
            task_abstract=task_abstract,
            is_collaborative_planning_enabled=comm_info.is_collaborative_planning_enabled,
        )
        result = LLMResult(
            content=f"[{self.name}]: {parsed_response['content']}",
            name=self.name,
            role="assistant",
        )
        logger.log_llm_result(result)
        comm_info.memory.add_messages(result)
        # update tasks by the task manager
        task_manager = self.task_manager_bank[comm_id]
        task_manager.update_task_manager(
            task_id,
            task_desc,
            task_abstract,
            assignee=self.name,
            status=TaskStatus.IN_PROGRESS,
        )
        self.comm_bank[comm_id] = comm_info
        self.task_manager_bank[comm_id] = task_manager
        await self._send_message(message_to_send)

    async def _handle_sync_task_assignment(self, new_message: AgentMessage, comm_id: str, obs_kwargs: dict = {}):
        """
        Handle the incoming sync task assignment message. The agent will inform the tool agent to execute the task.
        The discussion will be paused until the current agent returns the result.
        """
        comm_info: CommunicationInfo = self.comm_bank[comm_id]
        observation = self.observation_func(**obs_kwargs)

        (
            reference,
            task_desc,
            task_abstract,
            context_information,
            completion_criteria,
        ) = await self._rephrase_task_to_tool_agent(comm_id, observation)
        task_manager = self.task_manager_bank[comm_id]
        task_id = task_manager.create_task(task_desc, task_abstract, self.name, status=TaskStatus.TO_START)

        self.comm_bank[comm_id] = comm_info
        self.task_manager_bank[comm_id] = task_manager
        await self._call_tool_agent_and_inform(
            reference,
            task_desc,
            next_speaker=new_message.sender,
            comm_id=comm_id,
            task_id=task_id,
            task_abstract=task_abstract,
            context_information=context_information,
            completion_criteria=completion_criteria,
        )

    async def _coordination_discussion(
        self,
        new_message: AgentMessage | None,
        comm_id: str,
        obs_kwargs: dict = {},
    ):
        if not new_message or (
            new_message.type
            in [
                CommunicationType.DISCUSSION,
                CommunicationType.INFORM_TASK_RESULT,
                CommunicationType.INFORM_TASK_PROGRESS,
            ]
        ):
            await self._handle_info_message(new_message, comm_id, obs_kwargs)
        elif new_message.type == CommunicationType.ASYNC_TASK_ASSIGNMENT:
            await self._handle_async_task_assignment(new_message, comm_id, obs_kwargs)
        elif new_message.type == CommunicationType.SYNC_TASK_ASSIGNMENT:
            await self._handle_sync_task_assignment(new_message, comm_id, obs_kwargs)
        elif new_message.type == CommunicationType.CONCLUDE_GROUP_DISCUSSION:
            await self._conclude_group_discussion(comm_id)

    async def update_global_plan(self, comm_id: str):
        comm_info: CommunicationInfo = self.comm_bank[comm_id]
        task_manager: TaskManager = self.task_manager_bank[comm_id]
        prepend_prompt = [
            Template(self.system_prompt_template).safe_substitute(
                {
                    "name": self.name,
                    "desc": self.desc,
                    "agent_type": self.agent_type,
                    "agent_name": getattr(self.tool_agent, "agent_name", ""),
                    "agent_desc": getattr(self.tool_agent, "agent_desc", ""),
                }
            ),
            COMM_MAS_PROMPT,
            Template(COMM_COORDINATION_WITHOUT_GOAL_PROMPT).safe_substitute(
                {
                    "teammates": json.dumps(
                        [t for t in comm_info.team_members if t["name"] != self.name],
                        indent=2,
                    ),
                }
            ),
        ]

        task_management_view_message = {
            "role": "system",
            "content": Template(COMM_TASK_MANAGEMENT_APPEND_PROMPT).safe_substitute(
                {
                    "task_management_view": task_manager.tasks_view(),
                    "goal": comm_info.goal,
                }
            ),
        }
        append_msgs = []
        append_msgs.append(task_management_view_message)
        assert comm_info.is_collaborative_planning_enabled is True
        collaborative_plan_message = {
            "role": "system",
            "content": Template(COMM_PLANNER_PROMPT).safe_substitute(
                {
                    "task_management_view": task_manager.tasks_view(),
                    "goal": comm_info.goal,
                    "Dynamic_Collaborative_Planner": task_manager.get_latest_plan(),
                }
            ),
        }
        append_msgs.append(collaborative_plan_message)

        append_prompt = [Template(COMM_UPDATE_PLAN_APPEND_PROMPT).safe_substitute({"name": self.name})]

        response: LLMResult = await self.llm.agenerate_response(
            prepend_prompt=prepend_prompt,
            history=(await comm_info.memory.to_messages()) + append_msgs,
            append_prompt=append_prompt,
        )
        updated_plan = response.content
        print(f"updated_plan: {updated_plan}")
        return updated_plan

    async def tool_agent_run(self, task_desc: str):
        if self.tool_agent:
            return await self.tool_agent.run(task_desc)
        else:
            prepend_prompt = [f"{self.desc}"]
            response: LLMResult = await self.llm.agenerate_response(
                prepend_prompt=prepend_prompt,
                append_prompt=task_desc,
            )
            conclusion = response.content
            return conclusion

    async def _call_tool_agent_and_inform(
        self,
        reference: str | None,
        task_desc: str,
        next_speaker: str,
        comm_id: str,
        task_id: str,
        task_abstract: str,
        context_information: str,
        completion_criteria: str,
    ):
        goal_content_in_nested_team_up = f"""
# {task_abstract}
## Task Description
{task_desc}
## Task Inputs (including dialogues and takeaways from PREVIOUS collaboration)
{reference if reference else 'No inputs'}
## Context Information
{context_information}
## Completion Criteria
{completion_criteria}
"""
        task_content = f"""
# {task_abstract}
## Task Inputs (including dialogues and takeaways from PREVIOUS collaboration)
{reference if reference else 'No inputs'}
## Task Description
{task_desc}
"""
        comm_info: CommunicationInfo = self.comm_bank[comm_id]

        # TODO: complete the task assigned with a team or alone
        if self.support_nested_teams:
            team_up, thought_trajectory = await self._require_teamwork(task_content)

        else:
            team_up = False

        team_up_depth = comm_info.team_up_depth
        if team_up and (team_up_depth is None):
            # the agent decides to team up and there's no limit to the depth of teaming up
            task_conclusion = await self.launch_goal(
                # task_content,
                goal_content_in_nested_team_up,
                is_collaborative_planning_enabled=comm_info.is_collaborative_planning_enabled,
            )
        elif team_up and (team_up_depth >= 1):
            # the agent decides to team up and it's within the depth limit of teaming up
            task_conclusion = await self.launch_goal(
                # task_content,
                goal_content_in_nested_team_up,
                team_up_depth=team_up_depth - 1,
                is_collaborative_planning_enabled=comm_info.is_collaborative_planning_enabled,
            )
        elif team_up and (team_up_depth <= 0):
            # the agent decides to team up but it's out of the depth limit of teaming up
            task_conclusion = await self.tool_agent_run(task_content)
        else:
            # the agent decides not to team up or the config is set not to team up.
            task_conclusion = await self.tool_agent_run(task_content)

        await self._inform_task_result(task_desc, task_conclusion, next_speaker, comm_id, task_id, task_abstract)

    async def _require_teamwork(self, task: str) -> bool:
        local_contact = self.agent_contact.items()
        prepend_prompt = [
            Template(self.system_prompt_template).safe_substitute(
                {
                    "name": self.name,
                    "desc": self.desc,
                    "agent_type": self.agent_type,
                }
            )
        ]

        append_prompt = Template(COMM_WHETHER_TEAM_UP_PROMPT).safe_substitute(
            {
                "task": task,
                "retrieved_contact": str(local_contact),
            }
        )
        response: LLMResult = await self.llm.agenerate_response(
            prepend_prompt=prepend_prompt,
            append_prompt=append_prompt,
            response_format={"type": "json_object"},
        )
        parsed_response = response.content
        logger.log_llm_result(response)
        team_up = False if parsed_response["decision"] == "individual" else True
        thought_trajectory = parsed_response["thought"]
        print(parsed_response["thought"])

        return team_up, thought_trajectory

    async def _inform_task_result(
        self,
        task_desc: str,
        task_conclusion: str,
        next_speaker: str,
        comm_id: str,
        task_id: str,
        task_abstract: str,
    ):
        comm_info: CommunicationInfo = self.comm_bank[comm_id]
        task_result_inform = Template(EXEC_TASK_CONCLUSION_APPEND_PROMPT).safe_substitute(
            {"task_desc": task_desc, "task_conclusion": task_conclusion}
        )
        message_to_send = AgentMessage(
            content=task_result_inform,
            sender=self.name,
            comm_id=comm_id,
            next_speaker=next_speaker,
            state=CommunicationState.DISCUSSION,
            type=CommunicationType.INFORM_TASK_RESULT,
            task_id=task_id,
            task_desc=task_desc,
            task_conclusion=task_conclusion,
            task_abstract=task_abstract,
        )
        result = LLMResult(
            content=f"[{self.name}]: {task_result_inform}",
            name=self.name,
            role="assistant",
        )
        logger.log_llm_result(result)
        comm_info.memory.add_messages(result)
        task_manager: TaskManager = self.task_manager_bank[comm_id]
        task_manager.update_task_manager(
            task_id,
            task_desc,
            task_abstract,
            self.name,
            status=TaskStatus.COMPLETED,
            conclusion=task_conclusion,
            msg_in_memory=result,
        )
        if task_manager.is_triggered():
            if task_manager.trigger_setter == self.name:
                message_to_send.next_speaker = self.name
            task_manager.clear_triggers()
        self.comm_bank[comm_id] = comm_info
        self.task_manager_bank[comm_id] = task_manager

        await self._send_message(message_to_send)

    async def _rephrase_task_to_tool_agent(self, comm_id: str, observation: str = ""):
        comm_info: CommunicationInfo = self.comm_bank[comm_id]

        prepend_prompt = [
            Template(self.system_prompt_template).safe_substitute(
                {
                    "name": self.name,
                    "desc": self.desc,
                    "agent_type": self.agent_type,
                    "agent_name": getattr(self.tool_agent, "agent_name", ""),
                    "agent_desc": getattr(self.tool_agent, "agent_desc", ""),
                }
            ),
            COMM_MAS_PROMPT,
            Template(COMM_COORDINATION_WITHOUT_GOAL_PROMPT).safe_substitute(
                {
                    # "goal": comm_info.goal,
                    "teammates": json.dumps(
                        [t for t in comm_info.team_members if t["name"] != self.name],
                        indent=2,
                    ),
                }
            ),
        ]
        if observation != "":
            prepend_prompt.append(f"Current Observation:\n{observation}")

        messages = comm_info.memory.messages
        recent_history, recent_history_list = self._get_hybrid_recent_history(messages, comm_id)
        system_msg = {
            "role": "system",
            "content": Template(REPHRASE_TASK_HYBIRD_SYS_PROMPT).safe_substitute({"recent_history": recent_history}),
        }

        response: LLMResult = await self.llm.agenerate_response(
            prepend_prompt=prepend_prompt,
            history=[system_msg],
            append_prompt=Template(REPHRASE_TASK_APPEND_PROMPT).safe_substitute({"name": self.name}),
            response_format={"type": "json_object"},
        )
        parsed_response: dict = response.content
        task_desc = parsed_response["task_description"]
        message_index_list = parsed_response["index_to_integrate"]
        if not isinstance(message_index_list, list):
            try:
                message_index_list = json.loads(message_index_list)
            except json.JSONDecodeError:
                message_index_list = list(range(len(recent_history_list)))
        elif len(message_index_list) > 0 and any([not isinstance(i, int) for i in message_index_list]):
            message_index_list = list(range(len(recent_history_list)))
        thought = parsed_response["thought"]
        task_abstract = parsed_response["task_abstract"]
        context_information = parsed_response["context_information"]
        completion_criteria = parsed_response["completion_criteria"]

        print("======= task_rephrasing =======")
        print(f"thought:\n {thought}")
        print(f"message index list:\n {str(message_index_list)}")
        print(f"task_desc: {task_desc}")
        print(f"task_abstract: {task_abstract}")

        useful_information = []
        try:
            for msg_id in message_index_list:
                msg_id = int(msg_id)
                if msg_id <= len(recent_history_list):
                    useful_information.append(recent_history_list[msg_id - 1])
        except Exception as e:
            print(f"error while task rephrasing...{e}")
            import traceback

            traceback.print_exc()
        if len(useful_information) != 0:
            reference = "".join(useful_information)
        else:
            reference = None
        return (
            reference,
            task_desc,
            task_abstract,
            context_information,
            completion_criteria,
        )

    def _get_hybrid_recent_history(self, messages: list[LLMResult], comm_id: str) -> tuple[str, list[str]]:
        """Get hybrid recent history from chat history and task manager.
        Hybrid recent history consist of 5 latest messages from chat history and all tasks completed in task manager.

        Args:
            messages (list[LLMResult]): all messages of chat history from memory
            comm_id (str): use comm_id to fetch task manager in the group

        Returns:
            str: recent_history, which is string content of hybrid messages and tasks
            list: recent_history_str_list, which is a list of hybrid messages and tasks for reference, and each element is string.
        """
        comm_info: CommunicationInfo = self.comm_bank[comm_id]
        task_manager: TaskManager = self.task_manager_bank[comm_id]
        goal = comm_info.goal
        recent_history_list = []

        latest_num = 5
        current_msg_num = 0
        for msg in reversed(messages):
            if (
                isinstance(msg.content, str)
                and "Team, the following task is being executed in the background by myself." in msg.content
            ):
                continue
            elif isinstance(msg.content, str) and "Just a quick interruption to our current discussion." in msg.content:
                task = task_manager.msg2task.get(msg, None)
                if task:
                    recent_history_list.append(task)
            else:
                if current_msg_num < latest_num:
                    recent_history_list.append(msg)
                    current_msg_num += 1

        goal_LLMResult = LLMResult(
            content="[system]: The team is collaborating to solve this problem:\n" + goal,
            role="system",
        )
        recent_history_list.append(goal_LLMResult)
        # reverse the list in time order
        recent_history_list = recent_history_list[::-1]

        # get hybrid recent history in str format
        recent_history = ""
        recent_history_str_list = []
        task_id = 0
        for id, item in enumerate(recent_history_list):
            if isinstance(item, LLMResult):
                prefix = f"=== message index : {id+1} ===\n"
                content = item.to_openai_message()["content"] + "\n"
                recent_history += prefix + content
                recent_history_str_list.append(content)
            elif isinstance(item, TaskEntry):
                prefix = f"=== task index : {id+1} ===\n"
                content = str(item)
                recent_history += prefix + content
                recent_history_str_list.append(f"=== task index : {task_id} ===\n" + item.task2str_for_conclusion())
                task_id += 1

        return recent_history, recent_history_str_list

    def _number_items(self, history: list[dict], work_results: list[TaskEntry] | None) -> tuple[str, str, list]:
        """
        Select 3 latest message from history and all work_results as input for task rephrasing
        index each item and get `recent_history_str` (str), `work_results_str` (str)
        get `combined_list_with_index` as list and each item is str directly used in prompt for tool agent
        """
        history_without_task = []
        for item in history:
            if not (
                "Team, the following task is being executed in the background by myself." in item["content"]
                or "Just a quick interruption to our current discussion." in item["content"]
            ):
                # filter the message which is to inform the progess/completion of the task
                history_without_task.append(item)
        lastest_history = history_without_task[-5:]  # select 5 latest message from filtered history

        combined_list_with_index = []
        recent_history_str = ""
        work_results_str = ""
        id = 0

        for task in work_results:
            prefix = f"=== task index : {id} ===\n"
            content = str(task)
            item = prefix + content
            work_results_str += item
            combined_list_with_index.append(task.task2str_for_conclusion())
            id += 1

        for msg in lastest_history:
            prefix = f"=== message index : {id} ===\n"
            content = msg["content"]
            item = prefix + content + "\n"
            recent_history_str += item
            combined_list_with_index.append(content + "\n")
            id += 1

        if not work_results_str:
            work_results_str = "No tasks completed yet."

        return recent_history_str, work_results_str, combined_list_with_index

    async def _conclude_group_discussion(self, comm_id: str):
        """
        Let the agent conclude the group discussion.
        """
        comm_info: CommunicationInfo = self.comm_bank[comm_id]

        append_prompt = [Template(COMM_CONCLUDE_APPEND_PROMPT).safe_substitute({"goal": comm_info.goal})]
        history = await comm_info.memory.to_messages()
        if len(history) > 0:
            history[0]["content"] = "The history of the GROUP DISCUSSION:\n" + history[0]["content"]
        response: LLMResult = await self.llm.agenerate_response(
            history=history,
            append_prompt=append_prompt,
        )
        parsed_response = response.content
        message_to_send = AgentMessage(
            content=parsed_response,
            sender=self.name,
            comm_id=comm_id,
            state=CommunicationState.DISCUSSION,
            type=CommunicationType.CONCLUSION,
        )
        result = LLMResult(
            content=f"[{self.name}]: {message_to_send.content}",
            name=self.name,
            role="assistant",
        )
        logger.log_llm_result(result)
        comm_info.memory.add_messages(result)

        # conclusion should be recorded
        comm_info.conclusion = message_to_send.content
        comm_info.curr_turn = 0
        self.comm_bank[comm_id] = comm_info
        await self._send_message(message_to_send)

    async def _send_message(self, payload: AgentMessage):
        """Send a message to the chat session."""
        try:
            await self.server_websocket.send_message(payload.model_dump_json())
        except Exception as e:
            logger.error(f"Failed to send the message. {e}")
            return {"status": "failed", "message": str(e)}
        return {"status": "success"}

    async def _listen_message(self):
        while True:
            message = await self.server_websocket.receive_message()
            comm_id = message.comm_id
            logger.info(f"Received message: {str(message)}")
            match message.state:
                case CommunicationState.DISCUSSION | CommunicationState.VOTE:
                    await self.coordination(message, comm_id, max_turns=message.max_turns)
                # TODO: complete execution cases
                case _:
                    logger.error(f"Unknown state: {message.state}")

    async def shutdown(self):
        if self.tool_agent is not None:
            await self.tool_agent.shutdown()
