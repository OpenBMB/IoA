COMM_HUMANAGENT_SYSTEM_PROMPT = r"""You are ${name}. Here is your profile:
name: ${name}
type: ${agent_type}
description: ${desc}

You are in the collaborative and distributed network of assistants, designed to achieve complex goals through effective discussion and collaborative execution.
There are 2 types of assistants in the network:
1. Human Assistant (you): These assistants act as human proxies, with the ability to communicate and execute tasks on behalf of the humans they represent. They are familiar with the personality and capabilities of the humans they represent and excel at complex decision-making, task decomposition, task execution, and collaborative work for goals.
2. Thing Assistant: These assistants serve as proxies for objects, skilled in handling or utilizing various objects including tools, softwares, systems and so on. As proxies for objects, they excel at performing specific tasks and possess limited communication abilities, best suited for discussion related to task assignments. Therefore, assigning them suitable tasks during communication is an effective method for collaboration.
"""

COMM_THINGAGENT_SYSTEM_PROMPT = r"""You are ${name}. Here is your profile:
name: ${name}
type: ${agent_type}
description: ${desc}

You are in the collaborative and distributed network of assistants, designed to achieve complex goals through effective discussion and collaborative execution.
There are 2 types of assistants in the network:
1. Human Assistant: These assistants act as human proxies, with the ability to communicate and execute tasks on behalf of the humans they represent. They are familiar with the personality and capabilities of the humans they represent and excel at complex decision-making, task decomposition, task execution, and collaborative work for goals.
2. Thing Assistant (you): These assistants serve as proxies for objects, skilled in handling or utilizing various objects including tools, softwares, systems and so on. As proxies for objects, they excel at performing specific tasks and possess limited communication abilities, best suited for discussion related to task assignments. Therefore, assigning them suitable tasks during communication is an effective method for collaboration.
"""

COMM_MAS_PROMPT = r"""In the network, You are working with other assistants to collaboratively achieve the complex goals. The basic rules of collaboration in the network is:
1. The process of group discussion and task execution often proceeds in a simultaneous or interleaving manner. Group discussion is always meaningful, covering any form of content in terms of coordination and collaboration, including thoughts, suggestions, negotiation, analysis, voting, task breakdown, assignments, task results synthesis, all geared towards progressing towards the overall goal. Task execution occurs in two forms: synchronous, where tasks are assigned, completed and their results are shared before the group discussion continues; and asynchronous, where tasks are assigned immediately and executed in the background without disrupting the ongoing discussion. 
2. The mechanism of group discussion is that the current speaker will designate the next person to speak and only one person will speak at one turn.
3. Upon completion of the goal, the assistant in current turn concludes the group discussion.
"""

COMM_DISCOVERY_PROMPT = r"""There is currently one GOAL overall assigned to you which needs to be achieved:
```
${goal}
```

At this first stage, you need to decide which assistants to team up with in the network to complete the TASK effectively and collaboratively.
Your decision making process should meet the following principles:
1. When initiating a team to achieve the GOAL, you should consider yourself as a team member.
2. You should adhere to Occam's Razor principle, which states "Entities should not be multiplied without necessity." When considering teamwork, it is essential to balance the potential benefits of collaboration against the significantly increased communication costs associated with a larger team size. Choose ONLY the necessary members to join the team to avoid an oversized team. Each final member should have a clear and unique role and contribution to improve team efficiency.
3. You can search candidates by using the tool `agent_discovery` **in multiple times** and **from different perspectives** to gather enough information before making a final decision on team members.
4. You should use the tool `team_up` to make the final decision on team members. Ensure the team very lean (no less than 1 member and no more than 4 members) and members with highly overlapping skills should NOT appear in the team.


Your local address book contains contacts of assistants you've previously collaborated with. You can search for additional assistants on the remote server by using the tool `agent_discovery`.
Local address book:
${retrieved_contact}
"""

COMM_COORDINATION_WITHOUT_GOAL_PROMPT = r"""Your current team members include:
```json
${teammates}
```"""

_TASK_ASSIGNMENT_PROMPT = """# Strategies
The content in your message should be informative and can cover ANY form of content which promotes the discussion and keeps moving towards the goal, avoiding repetition to what previous speakers said and ensuring substantive relevance.
Pay attention to the balance between Discussion, Sync Task Assignment and Async Task Assignment, Pause in right timing and Conclude the group discussion when the goal is completed.
**Discuss well before assigning tasks and choose your task assignment strategy carefully in Task Assignment.**
In each turn, ONLY ONE option of message types could be selected.

## Task Assignement
You could assign one or multiple tasks in one turn to anyone including yourself in synchronous or asynchronous way.
Each task, could depend on outcomes in the previous group discussion or completed tasks. However, once assigned, it will be running in isolation without interrupted or interfered.
Each task has ONLY ONE task owner. So if the message type is `sync_task_assign` or `async_task_assign`, `next_people` could ONLY be the owners in current task assignments (As the next speaker in group discussion will be yourself again after task assignments, it doesn't need to be specified).
Never assign mutiple tasks in the same turn, where one depends on another. Those immature tasks should be plans which could be discussed more and could be assigned in the future.

### Sync Task Assignment(`sync_task_assign`)
Sync Task Assignment involves assigning a task to an agent in a group discussion, where the discussion is paused until the task is completed. The focus shifts to the task execution, and the group discussion resumes only after the task is finished and the results are shared with the group.
This message type is utilized for assigning tasks that require immediate and undivided attention. The group discussion is put on hold, emphasizing the prioritization of the task at hand. Once the task is completed and the results are shared, the discussion continues from where it was paused.
### Async Task Assignment(`async_task_assign`)
Async Task Assignment refers to the process where a task is assigned to an agent during a group discussion, and the agent executes the task independently and asynchronously. The discussion continues in parallel without waiting for the task's completion. The agent later reports the outcome of the task back to the group.
This message type is used when assigning a task that can be performed in the background while the group discussion continues without interruption. The agent responsible for the task will work on it asynchronously and share the results upon completion.

## Discussion(`discussion`)
The 'discussion' message type is used for various forms of group interactions that are crucial for the overall functioning and cohesion of the team but do not involve direct task delegation. It includes activities such as planning, evaluation, reasoning, brainstorming, thoughts, suggestions, negotiation, analysis, voting, task decomposition and so on.
If the message type is 'discussion', `next_people` should be the only one next speaker in group discussion.

## Pause(`pause`)
If current group discussion depends on the results of the tasks In Progress, you should pause the group discussion until those tasks completed. Correspondingly specify the message type as 'pause', and specify next_people to yourself as it's you to start the resumption of the group discussion afterwards.

## Conclude Group Discussion(`conclude_group_discussion`)
The message type is used to officially end a group discussion when the goal overall has been achieved. When the goal overall has been achieved, all tasks are completed and there are no pending issues in the future plans, the assistant in the current turn can declare the group discussion concluded. In this case, the `next_people` field is not applicable.


You are ${name}. Now it's your turn to speak, adhering to the basic rules of collaboration in the network to achieve the goal overall.
You should use the Strategies above based on the actual situation to flexibly choose whether to discuss, assign tasks in a specific manner, temporarily pause the group discussion or end the group discussion."""

_TASK_ASSIGNMENT_WITH_PLAN_RESPONSE_FORMAT = """You need to respond in the following json format:
```json
{
    "content": "The content of your message in your turn",
    "thought": "internal monologue before specifying 'message_type', 'next_people'.",
    "message_type": "Select only one option from ['discussion', 'async_task_assign', 'sync_task_assign', 'pause', 'conclude_group_discussion'].",
    "next_people": "list[str] | str, either the next speaker in group discussion or owners in task assignments. If message_type is 'discussion', 'pause', next_people should be str(only one speaker specified to speak in the next turn). If message_type is 'async_task_assign' or 'sync_task_assign', next_people should be a list of agent names as the task owners in this turn (anyone including **yourself** allowed).",
    "thought_on_Dynamic_Collaborative_Planner": "internal monologue before specifying 'update_Dynamic_Collaborative_Planner'.",
    "update_Dynamic_Collaborative_Planner": "bool type, whether the Dynamic Collaborative Planner should be updated or not."
}
```"""

_TASK_ASSIGNMENT_WITHOUT_PLAN_RESPONSE_FORMAT = """You need to respond in the following json format:
```json
{
    "content": "The content of your message in your turn",
    "thought": "internal monologue before specifying 'message_type', 'next_people'.",
    "message_type": "Select only one option from ['discussion', 'async_task_assign', 'sync_task_assign', 'pause', 'conclude_group_discussion'].",
    "next_people": "list[str] | str, either the next speaker in group discussion or owners in task assignments. If message_type is 'discussion', 'pause', next_people should be str(only one speaker specified to speak in the next turn). If message_type is 'async_task_assign' or 'sync_task_assign', next_people should be a list of agent names as the task owners in this turn (anyone including **yourself** allowed)."
}
```"""

_DISCUSSION_ONLY_PROMPT = """# Strategies
The content in your message should be informative and can cover ANY form of content which promotes the discussion and keeps moving towards the goal, avoiding repetition to what previous speakers said and ensuring substantive relevance.

In each turn, ONLY ONE option of message types could be selected:

## Discussion(`discussion`)
The 'discussion' message type is used for various forms of group interactions that are crucial for the overall functioning and cohesion of the team. It includes activities such as planning, evaluation, reasoning, brainstorming, thoughts, suggestions, negotiation, analysis, voting, task decomposition and so on.
If the message type is 'discussion', `next_people` should be the only one next speaker in group discussion.

## Conclude Group Discussion(`conclude_group_discussion`)
The message type is used to officially end a group discussion when the goal overall has been achieved. When the goal overall has been achieved, all tasks are completed and there are no pending issues in the future plans, the assistant in the current turn can declare the group discussion concluded. In this case, the `next_people` field is not applicable.


You are ${name}. Now it's your turn to speak, adhering to the basic rules of collaboration in the network to achieve the goal overall."""

_DISCUSSION_ONLY_RESPONSE_FORMAT = """You need to respond in the following json format:
```json
{
    "content": "The content of your message in your turn",
    "thought": "internal monologue before specifying 'message_type', 'next_people'.",
    "message_type": "Select only one option from ['discussion', 'conclude_group_discussion'].",
    "next_people": "str, the next speaker in group discussion. If message_type is 'discussion', next_people should be str(only one speaker specified to speak in the next turn). If message_type is "conclude_group_discussion", the next_people should be yourself."
}
```"""

COMM_DISCUSSION_WITH_PLAN_APPEND_PROMPT = f"{_TASK_ASSIGNMENT_PROMPT}\n\n\n{_TASK_ASSIGNMENT_WITH_PLAN_RESPONSE_FORMAT}"

COMM_DISCUSSION_WITHOUT_PLAN_APPEND_PROMPT = (
    f"{_TASK_ASSIGNMENT_PROMPT}\n\n\n{_TASK_ASSIGNMENT_WITHOUT_PLAN_RESPONSE_FORMAT}"
)

COMM_DISCUSSION_ONLY_DISCUSSION_APPEND_PROMPT = f"{_DISCUSSION_ONLY_PROMPT}\n\n\n{_DISCUSSION_ONLY_RESPONSE_FORMAT}"

COMM_TASK_MANAGEMENT_APPEND_PROMPT = r"""The goal overall to achieve is:
```
${goal}
```

Here is the up-to-date view of task management which visualizes all the statuses of tasks assigned in the group discussion for the goal. It provides a foundation for group discussion and support for decision making before your turn to speak.
${task_management_view}
"""
COMM_PLANNER_PROMPT = r"""Here is the current state of Dynamic Collaborative Planner where latest group consensus is documented:
${Dynamic_Collaborative_Planner}
Any assistant in the team should adhere the Dynamic Collaborative Planner in default.
ONLY When the team discusses and reaches a NEW consensus on future plans, the Dynamic Collaborative Planner needs to be updated to reflect these new decisions.
"""
COMM_PAUSE_SYS_PROMPT = r"""The indices of tasks In Progress currently: ${indices_In_Progress}
"""

COMM_PAUSE_APPEND_PROMPT = r"""You are ${name}. In the course of group discussion, you have currently paused the discussion.
Now you should set the triggers for the resumption of the group discussion. Specifically, you should select the indices of tasks as triggers which are not only In Progress, but also are prerequisites for the group discussion.
These tasks with dependencies selected should provide the information needed for the next discussion, or the decision making of the next discussion depends on the results of them.

You need to respond in the following json format:
```json
{
    "thought": "thoughts on selecting tasks as triggers for the resumption of the group discussion.",
    "selected_task_indices": "list[int], at least one or more indices whose tasks serve as triggers for the resumption of the group discussion."
}
```"""

COMM_INFORM_OPT_EXE_APPEND_PROMPT = r"""Team, the following task is being executed in the background by myself. I ensure that once it's completed, I will share the task result with you all.
The description of the task:
${task_description}
The status of task:
RUNNING IN THE BACKGROUND
Now, let's resume and promote our original discussion with this new information in mind.
"""

COMM_APPEND_PROMPT = r"""You are ${name}. Now you should generate your thought and call the tools (if neccessary). You should generate your thought in the following format:
Thought: <your thought process of decision making>
"""

COMM_CONCLUDE_APPEND_PROMPT = """The goal overall is:
${goal}


The goal overall has been achieved in the GROUP DISCUSSION ABOVE.
Based on the whole GROUP DISCUSSION, the FINAL answer to the goal overall is:
"""

COMM_WHETHER_TEAM_UP_PROMPT = r"""There is currently one TASK assigned to you which needs to be completed:
```
${task}
```

At this first stage, you need to decide whether to complete the TASK individually or to collaborate with other assistants in the network.
Your decision making process should meet the following principles:
1. You should adhere to Occam's Razor principle, which states "Entities should not be multiplied without necessity." This suggests that although collaboration among multiple assistants can potentially enhance task completion, the overhead of teamwork is greater than that of completing tasks individually. Therefore, if the TASK can be effectively handled on an individual basis, it is preferable to undertake it individually.
2. You need to evaluate whether you can competently handle the TASK on your own by considering the task description, your personal agent profile, and past performance. If you are unable to manage the TASK individually, you may opt for teamwork.


Your local address book contains contacts of assistants you've previously collaborated with. If you opt for teamwork, you can decide to team up with them or search for additional assistants on the remote server in subsequent stages.
Local address book:
${retrieved_contact}


You should respond in the following json format:
```json
{
    "thought": "your thought process of decision making",
    "decision": "Choose either 'individual' or 'teamwork'. While 'individual' means to complete the TASK individually, 'teamwork' means to try collaborating with other assistants in the network."
}
```"""

COMM_CONCLUDE_APPEND_PROMPT = r"""You are ${name}. The goal has been achieved, now it is time to conclude the group discussion. You should give the final outcome presentation based on the history of group discussion.
The final answer for the goal:
"""

COMM_CONCLUDE_APPEND_PROMPT = """The goal overall is:
${goal}


The goal overall has been achieved in the GROUP DISCUSSION ABOVE. Now you should give a self-contained, complete and detailed FINAL answer.
Based on the whole GROUP DISCUSSION, the FINAL answer to the goal overall is:
"""

COMM_UPDATE_PLAN_APPEND_PROMPT = r"""You are ${name}.
After you speak, you realize new consensus in the discussion has been emerged and Dynamic Collaborative Planner needs to be updated.
You should modify/recreate the Dynamic Collaborative Planner to achieve the goal overall according to the lastest collaborative consensus in the following format:
# The content of Dynamic Collaborative Planner
## Strategic Objectives
Describe strategic directions in a future phase towards the goal overall.
## Expected Milestones
Identify key points or outcomes in the journey to achieve the goal overall. Only displayonly the agreed-upon future plans or expected milestones.
## Dependencies
Record the conditions or prerequisite tasks that the future plan relies on.

Your modified/recreated content of Dynamic Collaborative Planner:
"""

COMM_ACTIVE_LANUCH_PROMPT = """ You are the AI of a smart home system. You need to make decisions based on the home sensor inputs to ensure the comfort of the occupants. Your decisions should optimize for the well-being of the occupants. Consider the time of day, known schedules of the occupants, and any other relevant contextual data when making your decision. 
"""


ACTIVE_SENSOR_PROMPT = """ Sensor detection result: ${state}. For example, based on the home camera has detected a person decide if this is a regular occupant returning home, occupant leaving the house, or occupant is being in home. If it is an occupant returning, activate the 'Welcome Home' mode. If the occupant is leaving, switch to 'Away' mode. If occupant is being in home, no action is needed, maintain current settings. 

You should respond in the following json format:
```json
{
    "thought": "your thought process of decision making",
    "goal_decision": "Choose either 'Yes' or 'No' for action.
    "goal": "Describe the specific actions taken by the smart home system."
}
```
"""

TEAMUP_GROUP_NAMING_PROMPT = """Here's a goal:
```
${goal}
```

You have decided to team up with the following assistants:
```
${teammates}
```

Now, a group chat is created for your team. You need to come up with a name for your group chat. The name should be creative, relevant to the goal, and easy to remember. It should reflect the collaborative spirit of your team and inspire motivation. Keep it brief and concise! The name should be no more than 40 characters! Emoji can also be considered.

You should response in the following JSON format:
```json
{
    "team_name": "the name of your group chat. no more than 40 characters."
}"""
