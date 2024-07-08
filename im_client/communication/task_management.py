from __future__ import annotations
from enum import Enum
import uuid
from common.types.llm import LLMResult
from common.utils.database_utils import Serializable
from common.log import logger


class TaskStatus(Enum):
    TO_START = (0, "To Start")
    IN_PROGRESS = (1, "In Progress")
    COMPLETED = (2, "Completed")
    # ON_HOLD = "On Hold"
    FAILED = (2, "Failed")

    # PENDING = "Pending"
    def __init__(self, priority: int, description: str):
        self.priority = priority
        self.description = description


class TaskAssignmentRespondManager(Serializable):
    """
    Mechanism for Synchronous/Asynchronous Task Allocation:
    After allocating tasks, it is necessary to receive feedback signals from
    all assigned agents before proceeding with the discussion.
    """

    def __init__(self, comm_id: str):
        self.comm_id = comm_id
        self.await_agents = set()

    def register_await_agents(self, agents: list[str]):
        self._clear()
        self.await_agents.update(agents)

    def _clear(self):
        self.await_agents.clear()

    def update_await_agents(self, await_agent: str):
        self.await_agents.discard(await_agent)

    def check_empty(self) -> bool:
        return len(self.await_agents) == 0

    def to_dict(self) -> dict:
        return {
            "comm_id": self.comm_id,
            "await_agents": list(self.await_agents),
        }

    @staticmethod
    def from_dict(data: dict) -> TaskAssignmentRespondManager:
        manager = TaskAssignmentRespondManager(comm_id=data["comm_id"])
        manager.await_agents = set(data.get("await_agents", []))
        return manager


class TaskEntry(Serializable):
    def __init__(
        self,
        task_id: str,
        task_desc: str,
        task_abstract: str,
        assignee: str,
        status=TaskStatus.TO_START,
    ):
        self.__task_id: str = task_id
        self.__task_desc: str = task_desc
        self.__task_abstract: str = task_abstract
        self.__assignee: str = assignee
        # TODO: determine to save __task_input or not
        self.status: TaskStatus = status
        self.conclusion: str | None = None

    @property
    def task_id(self):
        return self.__task_id

    @property
    def task_desc(self):
        return self.__task_desc

    @property
    def assignee(self):
        return self.__assignee

    @property
    def task_abstract(self):
        return self.__task_abstract

    # @property
    # def task_input(self):
    #    return self.__task_input

    def update_status(self, new_status: TaskStatus):
        if self.status.priority <= new_status.priority:
            self.status = new_status

    def update_conclusion(self, conclusion: str):
        self.conclusion = conclusion

    def update(self, status: TaskStatus, **kwargs):
        self.update_status(status)
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __str__(self):
        return f"""Assignee: {self.__assignee}
Task abstract: {self.__task_abstract}
Status: {self.status.description}
"""

    def task2str_for_conclusion(self):
        return f"""Assignee: {self.__assignee}
Task abstract: {self.__task_abstract}
Task conclusion:
{self.conclusion}
"""

    def to_dict(self) -> dict:
        return {
            "task_id": self.__task_id,
            "task_desc": self.__task_desc,
            "task_abstract": self.__task_abstract,
            "assignee": self.__assignee,
            "status": self.status.name,  # Assuming status is an Enum and we store the name
            "conclusion": self.conclusion,
        }

    @staticmethod
    def from_dict(data: dict) -> TaskEntry:
        task_entry = TaskEntry(
            task_id=data["task_id"],
            task_desc=data["task_desc"],
            task_abstract=data["task_abstract"],
            assignee=data["assignee"],
            status=TaskStatus[data["status"]],  # Assuming TaskStatus is an Enum
        )
        task_entry.conclusion = data.get("conclusion")  # Use .get() to handle potential absence of 'conclusion'
        return task_entry


class TaskManager(Serializable):
    """
    Task management, primarily used for the entire process of task allocation, execution, and completion.
    """

    def __init__(self, comm_id: str):
        self.__global_index = 0  # next task index in task manager
        self.task_assign_manager = TaskAssignmentRespondManager(comm_id)
        self.tasks: dict[str, tuple[int, TaskEntry]] = {}  # {task_id, (task_index,task_entry)}
        self.taskIndex2tasks: dict[int, TaskEntry] = {}
        self.triggers: dict[
            str, bool
        ] = {}  # a dict of task ids, each task id will be mapped into True/False to mark whether the task is in terminated status or not.
        self.trigger_setter: str | None = None  # the name of assistant who sets the triggers
        # TODO: How to ensure that at any point, only one trigger_setter at most is permitted.
        self.previous_triggers_status: bool = True  # True if check_triggers returned True before update.
        self.current_triggers_status: bool = True  # True if check_triggers returns True after update.
        self.msg2task: dict[LLMResult, TaskEntry] = {}

        self.dynamic_collaborative_planner: list[str] = ["No collaborative consensual plans shaped yet."]

    def _create_task_index(self):
        task_index = self.__global_index
        self.__global_index += 1
        return task_index

    def create_task(
        self,
        task_desc: str,
        task_abstract: str,
        assignee: str,
        status: TaskStatus = TaskStatus.TO_START,
        task_id: str | None = None,
    ):
        # create task_id
        # TODO: the task_id should be assured that it's unique in global
        if not task_id:
            task_id = uuid.uuid4().hex
        task_entry = TaskEntry(task_id, task_desc, task_abstract, assignee, status)
        task_index = self._create_task_index()
        self.tasks[task_id] = (task_index, task_entry)
        self.taskIndex2tasks[task_index] = task_entry
        return task_id

    def update_task_manager(
        self,
        task_id: str,
        task_desc: str,
        task_abstract: str,
        assignee: str,
        status: TaskStatus,
        **kwargs,
    ):
        # update the tasks
        _, task = self.tasks.get(task_id, (None, None))
        if task:
            logger.info(
                f"Update task {task_id}.\nTo update: {str(kwargs)}\nAfter update: {str(task)}\nUpdated Status: {str(status)}"
            )
            task.update(status, **kwargs)
        else:
            logger.info(f"Create task {task_id}. {str(kwargs)}")
            # when task_id is not in task manager, create one with task_id
            self.create_task(task_desc, task_abstract, assignee, status, task_id)
            _, task = self.tasks.get(task_id, (None, None))
            task.update(status, **kwargs)
        logger.info(f"self.triggers: {self.triggers}")
        # update the triggers
        if (status.priority == TaskStatus.COMPLETED.priority) and task_id in self.triggers:
            logger.info(f"Update triggers {task_id} to True.")
            self.previous_triggers_status = self.current_triggers_status

            self.triggers[task_id] = True

            self.current_triggers_status = self.check_triggers()

        # update the msg2task
        if status.priority == TaskStatus.COMPLETED.priority:
            # hook msg2task
            if "msg_in_memory" in kwargs:
                msg_in_memory = kwargs["msg_in_memory"]
                self.hook_msg2task(task_id, msg_in_memory)

    def hook_msg2task(self, task_id: str, msg_in_memory: LLMResult):
        """
        map message in memory with corresponding task

        The preconditions are:
        task_id has been registered in task manager.
        """
        _, task = self.tasks.get(task_id, (None, None))
        if task:
            self.msg2task[msg_in_memory] = task

    def tasks_view(self):
        content = ""
        head = "The view of task management:\n"
        content += head
        for task_index, task in self.tasks.values():
            prefix = f"=== task index : {str(task_index)}===\n"
            content += prefix + str(task)

        if len(self.tasks) == 0:
            content += "No tasks existed\n"

        return content

    def tasks_filter_by_status(self, status: TaskStatus | None | list[TaskStatus]):
        result = []
        for _, task in self.tasks.values():
            if status is None or task.status == status or (isinstance(status, list) and task.status in status):
                result.append(task)

        return result

    def indices_filter_by_status(self, status: TaskStatus | None | list[TaskStatus]) -> list[str]:
        result = []
        for task_index, task in self.tasks.values():
            if status is None or task.status == status or (isinstance(status, list) and task.status in status):
                result.append(task_index)
        return str(result)

    def is_triggers_empty(self) -> bool:
        return len(self.triggers) == 0

    def set_triggers(self, task_identifiers: list[int] | list[str], trigger_setter: str) -> tuple[bool, list[str]]:
        """Set triggers for the resumption of the group discussion.

        Args:
            task_identifiers (list[int]|list[str]):
            selected task indices or ids where tasks should be set as triggers for the resumption of the group discussion.
            Each element in `task_identifiers` is either task index (int), or task id (str).

        Returns:
            bool: If there are tasks In Progress whose task indices are in `task_identifiers`
                (which means there are substantive triggers to set), the return value should be set True. False otherwise.
            list[str]: the list of task ids. The task of each task id exists in self.task_manager and is not in terminated status.
        """
        assert self.is_triggers_empty()
        # self.triggers.clear()
        task_ids = []

        for task_identify in task_identifiers:
            if isinstance(task_identify, str):
                # task id
                task_id = task_identify
                task = None if not self.tasks.get(task_id, None) else self.tasks.get(task_id, None)[-1]
                task_ids.append(task_id)
            elif isinstance(task_identify, int):
                # task index
                task_index = task_identify
                task = self.taskIndex2tasks.get(task_index, None)
                if task:
                    task_ids.append(task.task_id)

            if task:
                if task.status.priority < TaskStatus.COMPLETED.priority:
                    logger.info(f"Set {task.task_id}'s trigger")
                    self.triggers[task.task_id] = False
                else:
                    logger.info(f"{task.task_id} is in terminated status. Skip setting trigger.")
                    self.triggers[task.task_id] = True
        logger.info(f"Triggers: {self.triggers}")

        self.previous_triggers_status = self.current_triggers_status
        self.current_triggers_status = self.check_triggers()

        if self.is_triggers_empty() or self.check_triggers():
            """
            if triggers is empty or all the tasks in triggers are in terminated status
            """
            trigger_set = False
            self.trigger_setter = None
            self.clear_triggers()

            return trigger_set, task_ids
        else:
            trigger_set = True
            self.trigger_setter = trigger_setter
            return trigger_set, task_ids

    def update_triggers(self, task_identifiers: list[int] | list[str], trigger_setter: str) -> tuple[bool, list[str]]:
        """Update triggers for the resumption of the group discussion.

        The function is different from `set_triggers()` in that `set_triggers()` is used by the assistant who initiated PAUSE,
        while `update_triggers()` is used to update the others' task manager, considering latency in
        message delivery and state inconsistencies in the distributed network.

        Specifically, the difference is in the handling of `task_identifiers`. `task_identifiers` will
        be filtered first in `set_triggers()` to eliminate the effects of hallucination of LLM-generated content,
        while the element in `task_identifiers` which is not in task manager (because of latency
        in message delivery) will be saved in `update_triggers()`.


        Args:
            task_identifiers (list[int]|list[str]):
            selected task indices or ids where tasks should be set as triggers for the resumption of the group discussion.
            Each element in `task_identifiers` is either task index (int), or task id (str).

        Returns:
            bool: If there are tasks In Progress whose task indices are in `task_identifiers`(which
                means there are substantive triggers to set), the return value should be set True. False otherwise.
            list[str]: the list of task ids.
        """
        assert self.is_triggers_empty()

        task_ids = []

        for task_identify in task_identifiers:
            assert isinstance(task_identify, str)
            # task id
            task_id = task_identify
            task = None if not self.tasks.get(task_id, None) else self.tasks.get(task_id, None)[-1]
            task_ids.append(task_id)

            if task:
                if task.status.priority < TaskStatus.COMPLETED.priority:
                    # not in terminated status
                    logger.info(f"Set {task_id}'s trigger")
                    self.triggers[task.task_id] = False
                else:
                    logger.info(f"{task_id} is in terminated status. Skip setting trigger.")
                    self.triggers[task.task_id] = True
            else:
                self.triggers[task_id] = False

        self.previous_triggers_status = self.current_triggers_status
        self.current_triggers_status = self.check_triggers()
        logger.info(f"previous_triggers_status: {self.previous_triggers_status}")
        logger.info(f"current_triggers_status: {self.current_triggers_status}")
        logger.info(f"Triggers: {self.triggers}")

        if self.is_triggers_empty() or self.check_triggers():
            """
            if triggers is empty or all the tasks in triggers are in terminated status
            """
            trigger_set = False
            self.trigger_setter = None
            self.clear_triggers()

            return trigger_set, task_ids
        else:
            trigger_set = True
            self.trigger_setter = trigger_setter
            return trigger_set, task_ids

    def check_triggers(self) -> bool:
        """check whether tasks in triggers are ALL in terminated status or not.

        Returns:
            bool: True if the tasks in triggers are ALL in terminated status. False otherwise.
            If the triggers is empty, return True in default.
        """
        for _, status in self.triggers.items():
            if not status:
                return False
        return True

    def is_triggered(self) -> bool:
        return not self.previous_triggers_status and self.current_triggers_status

    def clear_triggers(self):
        self.triggers.clear()
        self.trigger_setter = None
        self.previous_triggers_status = True
        self.current_triggers_status = True

    def get_latest_plan(self):
        return self.dynamic_collaborative_planner[-1]

    def update_plan(self, plan: str):
        self.dynamic_collaborative_planner.append(plan)

    def to_dict(self) -> dict:
        return {
            "__global_index": self.__global_index,
            "task_assign_manager": self.task_assign_manager.to_dict(),
            "tasks": {
                task_id: (task_index, task_entry.to_dict()) for task_id, (task_index, task_entry) in self.tasks.items()
            },
            "taskIndex2tasks": {index: task_entry.to_dict() for index, task_entry in self.taskIndex2tasks.items()},
            "triggers": self.triggers,
            "trigger_setter": self.trigger_setter,
            "__previous_triggers_status": self.previous_triggers_status,
            "__current_triggers_status": self.current_triggers_status,
            # the key should be string type for json serilization.
            "msg2task": {result.model_dump_json(): task.to_dict() for result, task in self.msg2task.items()},
            "dynamic_collaborative_planner": self.dynamic_collaborative_planner,
        }

    @staticmethod
    def from_dict(data: dict) -> TaskManager:
        manager = TaskManager(
            comm_id=data["task_assign_manager"]["comm_id"]
        )  # Assuming comm_id can be extracted like this
        manager._restore_inner_properties(
            data["__global_index"],
            data["__previous_triggers_status"],
            data["__current_triggers_status"],
        )
        manager.task_assign_manager = TaskAssignmentRespondManager.from_dict(data["task_assign_manager"])
        manager.tasks = {
            task_id: (task_index, TaskEntry.from_dict(task_entry_dict))
            for task_id, (task_index, task_entry_dict) in data["tasks"].items()
        }
        manager.taskIndex2tasks = {
            index: TaskEntry.from_dict(task_entry_dict) for index, task_entry_dict in data["taskIndex2tasks"].items()
        }
        manager.triggers = data["triggers"]
        manager.trigger_setter = data["trigger_setter"]
        manager.msg2task = {
            LLMResult.model_validate_json(result_json): TaskEntry.from_dict(task_dict)
            for result_json, task_dict in data["msg2task"].items()
        }
        manager.dynamic_collaborative_planner = data["dynamic_collaborative_planner"]
        return manager

    @property
    def global_index(self):
        return self.__global_index

    def _restore_inner_properties(
        self,
        global_index: int,
        previous_triggers_status: bool,
        current_triggers_status: bool,
    ):
        self.__global_index = global_index
        self.previous_triggers_status = previous_triggers_status
        self.current_triggers_status = current_triggers_status


from pydantic import BaseModel
from typing import Any, TYPE_CHECKING


class Demo(BaseModel):
    comm_id: str
    goal: str
    memory: Any


if __name__ == "__main__":
    """
    demo = Demo(comm_id="1", goal="test", memory=None)
    demo_str = demo.model_dump_json()  # pydantic model to json string
    print(demo_str)
    demo_recoverd = Demo.model_validate_json(demo_str)  # json string to pydantic model
    print(demo_recoverd)
    """
    task_manager = TaskManager(comm_id="123")
    task_manager.create_task(
        task_desc="test",
        task_abstract="test the serialization and deserialization.",
        assignee="human",
    )
    print(task_manager.to_dict())
    demo = TaskManager.from_dict(task_manager.to_dict())
    print(demo)
    print(demo.to_dict())
    import json

    print(isinstance(TaskManager.from_dict(json.loads(json.dumps(demo.to_dict()))), TaskManager))
