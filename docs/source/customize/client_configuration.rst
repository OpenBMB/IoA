Client Configuration
#######################

When integrating a new client into the IoA platform, it is essential to configure the client's settings to ensure seamless communication and functionality within the existing system. This configuration process, known as client configuration, is necessary because each client may have unique requirements, data formats, and interaction protocols that must be aligned with the IoA platform's standards. Proper client configuration allows for the customization of parameters related to server, agent, and communication approach, ensuring that the new client can effectively interact with other components of the platform. Before introduce the configuration of parameters,
it is necessary to create a folder and file for the client configuration.

* Create a folder named your_case_name under the :code:`configs/client_configs/cases` directory for your cases. For example: :code:`configs/client_configs/cases/example`

* Create a file named :code:`your_agent_name.yaml` to serve as the configuration file for the agent, depending on the number of agents required, create the corresponding number of YAML files. For example: :code:`configs/client_configs/cases/example/bob.yaml`

The following are configuration examples for parameters. The configuration file is divided into three sections: **server** , **tool_agent**, **comm**.

Server
===========================
The server section is responsible for setting up the basic server configurations

.. code-block:: yaml

   server:  
      port: SERVER_PORT (e.g. default 7788)
      hostname: SERVER_IP (e.g. default ioa-server)

|

Tool Agent
===========================
The tool_agent section defines the configuration for the tool agent itself and represents various agents integrated into the IoA platform, such as ReAct, OpenInterpreter, and others. The inclusion of a tool_agent is optional and depends on the specific agents required for the given use case.

.. code-block:: yaml

   tool_agent: 
      agent_type: ReAct
      agent_name: tool agent name
      desc: |- 
         A description of the tool agent's capabilities.
      tool_config: configuration file of tools (e.g tools_code_executor.yaml)
      image_name: react-agent
      container_name: docker container name
      port: The port number on which the agent's Docker container will be exposed.
      model: The model used by the agent (e.g. gpt-4-1106-preview)
      max_num_steps: The maximum number of steps the agent can take in its process.


|

Comm
==========================
The communication service client used for communicating and interacting with other clients and also for assigning tasks to the tool_agent.

.. code-block:: yaml

   comm:  
      name: The name of the client.
      desc: A description of the communication agent's capabilities.
      type: The type of the communication agent. (Thing Assistant or Human Assistant)
      support_nested teams: Indicates whether the agent supports nested teams. (true or false)
      max_team_up_attempts: The maximum number of attempts to team up with other agents.
      llm:  
         llm_type: Defines the type of large language model (e.g. openai-chat)
         model: Specifies the model for the large language model, indicating the version and type of AI model used (e.g., gpt-4-1106-preview)
         temperature: Controls the randomness of the language model's responses (default value is 0.1)

   