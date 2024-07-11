Integrate Third-party Agent
################################

Here is a brief guide for integrating third-party agents. If you want to integrate an agent from a third-party repository, there are mainly two things to consider:


* **Build and Expose a Docker Container**:
  
  * **Containerization**: Package the third-party agent within a Docker container. This ensures a consistent and isolated environment for the agent to run.


* **Develop an Adapter for Integration**:
  
  * **Expose an API Interface**: Utilize FastAPI or another suitable web framework to expose a run interface externally. The interface should have the following specification:
  
    * **run(task_desc)**: Executes the task_desc task from scratch and returns the result as a string.

You can review the implemented logic for the specific example, Open Interpreter, located at :code:`im_client/agents/open_interpreter`. The detailed explanation of this example is given in the following section.

|

Open Interpreter Integration
===============================
* **Building an HTTP service for Open Interpreter**: 
  
  * The Open Interpreter, located in the :code:`im_client/agents/open_interpreter/open_interpreter_agent.py` script, will be dockerized. This script includes FastAPI POST endpoints, which will be exposed as an HTTP service when started with Uvicorn. When deployed with Docker, these endpoints can be accessed externally.

* **Creating Dockerfile for Open Interpreter**: 
  
  * Next, create a Dockerfile in the :code:`dockerfiles/tool_agents` directory. This Dockerfile ensures that tool agents like Open Interpreter can be started with Docker, preventing potential environment conflicts with IoA.

* **Building Adapter for Open Interpreter**: 
  
  * The adapter for Open Interpreter, also located in :code:`im_client/agents/open_interpreter/open_interpreter_agent.py`, facilitates bridges the gap between the protocol of IoA and Open Interpreter. It converts and forwards requests to the Open Interpreter Docker container.
  
*  **Building configuration file for Open Interpreter**: 
    
   * An example configuration file for Open Interpreter is located in :code:`configs/client_configs/cases/example/open_interpreter.yaml`. For the explanation of configuration parameters refers to `Client Configuration Section <client_configuration.html>`_.

|

Open Interpreter Docker Startup
=======================================
* Environment Variable Configuration:
  
  * In the :code:`dockerfiles/compose/open_interpreter.yaml`, set up the environment variable :code:`CUSTOM_CONFIG` to specify the configuration file for the tool agent. Define the tool agent-related parameters in the file referenced by :code:`CUSTOM_CONFIG`. For example, the configuration file for Open Interpreter is:
  
    .. code-block:: yaml

      CUSTOM_CONFIG=configs/cases/open_interpreter.yaml
  
  * In the :code:`dockerfiles/compose/.env`, ensuer to set up the necessary environment variable such as :code:`OPENAI_API_KEY`, :code:`OPENAI_RESPONSE_LOG_PATH`.

* Building and Running the Docker Container:
  
  * Build the Dockerfile previously created by running the following command in the terminal:
   
    .. code-block:: bash

      docker build -f dockerfiles/tool_agents/open_interpreter.Dockerfile -t open_interpreter:latest .
  
  * Then, start the server and communication agents by running:
  
    .. code-block:: bash

      docker-compose -f dockerfiles/open_interpreter.yml up






