REPHRASE_TASK_HYBIRD_SYS_PROMPT = r"""The recent chat history and completed tasks so far in the group discussion:
${recent_history}
"""

REPHRASE_TASK_APPEND_PROMPT = r"""You are ${name}. During the group discussion to achieve the goal, you've been assigned a specific task in LATEST LAST turn. 
Now you should identify the task assigned to YOU currently and rephrase it from the recent chat history, and incorporate substantive work results of tasks in dependency and necessary information of messages in recent chat history as the task input. 
This rephrased task description should be clear, concise, complete, specific, and aligned with the global goal, ensuring you fully understand the requirements and steps for successful completion. The latest last message in the group discussion is key to rephrase the task assigned to You.
If necessary, you should list the indices in 'index_to_integrate' to incoporate content into task input. If the index is message index, the message itself will be integrated. If the index is task index, the substantive **work result** of the task will be integrated.
The consequences of missing essential information are severe, so you need to ensure that the recall rate for the indices which should be integrated reaches 100%.

The rephrased task description and the task input incorporated will serve as all the information source and guide for you to execute the task effectively.

You must respond in the following json format:
```json
{
    "thought": "think deeply on the task description and index selection to integrate content into the task input",
    "task_description": "your rephrased complete task description",
    "task_abstract": "summarize the task description and keep it concise and clear with all the key components.",
    "index_to_integrate": "list[int], a list of indices whose information (like messages or substantive work results of tasks) is not covered in 'task_description' and should be integrated in the task input during post processing. [] means nothing is necessary to be incorporated in the task input."
}
```"""
REPHRASE_TASK_APPEND_PROMPT = r"""You are ${name}.
During the group discussion to achieve the goal overall (which is the message with index 1), you are being assigned a specific task in LATEST LAST turn. 
Now you should identify the task assigned to YOU currently and rephrase it from the recent chat history and completed tasks so far into a clear, complete and self-contained version in well-defined format.
The rephrased task should be clear, complete, specific, contain everything you need to complete successfully. 
The rephrased task is well formatted, which includes 4 components:
# The Rephrased Task
## Task Abstract(`task_abstract`)
A concise and descriptive title that captures the essence of the task, making it easy to understand at a glance.
## Task Description(`task_description`)
A clear and detailed description of the task that needs to be accomplished.
## Task Inputs(to fill the field of `index_to_integrate` by selecting indices)
Comprehensive information is very critical for the successful completion of the current task.
You should list the indices in `index_to_integrate` to incoporate any helpful content (including the goal overall if neccessary) garnered from previous collaborations into task input. If the index is message index, the message itself will be integrated. If the index is task index, the substantive **work result** of the task will be integrated.
## Context Information(`context_information`)
Provide essential background information that elucidates the task's relevance and its role within the broader project scope. 
This section should elucidate how the task inputs are connected to the task execution. It should also introduce the broader project briefly, articulate how the task aligns with collaborative efforts within the broader project, pinpointing specific considerations to avoid any redundant or overlapping activities.

## Completion Criteria(`completion_criteria`)
Define specific, measurable criteria that will be used to evaluate whether the task has been successfully completed. These criteria could include qualitative benchmarks, quantitative metrics or any other standards agreed upon by the team.

The Rephrased Task will serve as **all the information source** and guide for you to execute the task effectively.

You must respond in the following json format:
```json
{
    "thought": "internal monologue when rephrasing the task assigned to you",
    "task_abstract": "",
    "task_description": "",
    "index_to_integrate": "list[int], a list of indices whose information (like messages or substantive work results of tasks) is not covered in 'task_description' and should be integrated in the task input during post processing. [] means nothing is necessary to be incorporated in the task input.",
    "context_information": "",
    "completion_criteria": ""
}
```"""

EXEC_TASK_CONCLUSION_APPEND_PROMPT = """Just a quick interruption to our current discussion. I have an important update regarding the task I've been working on alongside our group discussion.
Task Description:
${task_desc}
The task has now been completed. Here are the key outcomes:
Task Conclusion:
${task_conclusion}
Now, let's resume and promote our original discussion with this new information in mind.
"""
