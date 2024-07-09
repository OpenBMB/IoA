Code Structure
######################

1. :code:`im_client/agents`:This directory houses the different tool agents. The following are the currently supported Agents. For information on how to integrate a new agent, please refer to the description of `Customize Tool Agent <customize_tool_agent.html>`_

   * **ReAct Agent**: :code:`im_client/agents/react`
   * **OpenAI Assistant**: :code:`im_client/agents/openai_assistant`
   * **Open Interpreter**: :code:`im_client/agents/open_interpreter`
   * **AutoGPT**: :code:`im_client/agents/autogpt`

|
  
1. :code:`im_client/communication`: The specific implementation of the Communication Layer. The file communication_layer.py implements the main logic, main.py is the entry point for starting, and task_management.py maintains the status of all ongoing/completed tasks in the current group chat (which will be given to the agents as part of the prompt).

|

3. :code:`im_client/server`: Implementation of the central server, including the agent registry, session manager, etc.

|

4. :code:`im_client/config`: Stores some config files for agents. When the entire system is started using docker-compose, it reads the config specified in the docker-compose configuration. Additionally, the tools folder in this directory contains some yaml descriptions of tools.

|

5. :code:`im_client/tools`: Contains the concrete implementations of some tools, and their descriptions are stored in the aforementioned im_client/config/tools.

|

6. :code:`im_client/llms`: Currently, only the OpenAI interface has been implemented, meaning the communicative agent's LLM temporarily only supports the OpenAI models.

|

7. :code:`im_client/memory`: So far, the simplest list memory is basically used, which is to store all messages exactly as they are received.


|

8. :code:`im_client/prompts`: Stores nearly all the prompts used in the framework.

|

9. :code:`im_client/types`: Some data types used in the framework, with type annotations using pydantic, such as task descriptions, task statuses, etc.

|

10. :code:`dockerfiles`: Contains all the dockerfiles for building the docker images for agents and for starting the entire system with docker-compose.

