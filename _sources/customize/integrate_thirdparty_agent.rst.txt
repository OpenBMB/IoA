Integrate Third-party Agent
################################

|

Here is a brief guide for integrating third-party agents. If you want to integrate an agent from a third-party repository, there are mainly two things to consider:


* **Build and Expose a Docker Container**:
  
  * **Containerization**: Package the third-party agent within a Docker container. This ensures a consistent and isolated environment for the agent to run.
  * **Expose an API Interface**: Utilize FastAPI or another suitable web framework to expose a run interface externally. The interface should have the following specification:
  
    * **run(task_desc)**: Executes the task_desc task from scratch and returns the result as a string.


* **Develop an Adapter for Integration**:
  
  * **Data Format Conversion**: Write an adapter to facilitate communication between the third-party agent and IoA. This involves converting data formats to ensure compatibility. For instance, convert memory information in IoA, which uses :code:`LLMResult` from :code:`/types/llm.py`, into a format that the third-party agent can process.
  * **Interface Invocation**: The adapter acts as an intermediary, invoking the API provided by the Docker container created in the first step. This ensures seamless interaction between IoA and the third-party agent.

You can review the implemented logic for the specific example, Open Interpreter, located at :code:`im_client/agents/open_interpreter`. The detailed explanation of this example is given in the following section.

|

Open Interpreter Integration
===============================
* **Building an HTTP service for Open Interpreter**: 
  
  * The Open Interpreter, located in the :code:`im_client/agents/open_interpreter` directory, will be dockerized. This directory includes FastAPI POST endpoints, which will be exposed as an HTTP service when started with Uvicorn. When deployed with Docker, these endpoints can be accessed externally.

* **Creating Docker for Open Interpreter**: 
  
  * Next, create a Dockerfile in the :code:`dockerfiles/tool_agents` directory. This Dockerfile ensures that tool agents like Open Interpreter can be started with Docker, preventing potential environment conflicts with IoA.

* **Building Adapter for Open Interpreter**: 
  
  * The adapter for Open Interpreter, also located in :code:`im_client/agents/open_interpreter` , facilitates data format conversion between IoA and Open Interpreter. It forwards requests to the Open Interpreter Docker container. The adapter provides a run method that converts data formats and sends a POST request to the corresponding endpoint of the Open Interpreter Docker container.

|

Open Interpreter Docker Startup
=======================================
* Environment Variable Configuration:
  
  * In the :code:`open_instruction.yml`, set up the environment variable :code:`CUSTOM_CONFIG` to specify the configuration file for the tool agent. Define the tool agent-related parameters in the file referenced by :code:`CUSTOM_CONFIG`. For example, the configuration file for Open Interpreter is:
  
    .. code-block:: yaml

      CUSTOM_CONFIG=configs/cases/open_instruction/open_interpreter.yaml
  
  * In the :code:`dockerfiles/compose/.env_template`, ensuer to set up the necessary environment variable such as :code:`OPENAI_API_KEY`, :code:`OPENAI_RESPONSE_LOG_PATH`.

* Building and Running the Docker Container:
  
  * Build the Dockerfile previously created by running the following command in the terminal:
   
    .. code-block:: bash

      docker build -f dockerfiles/tool_agents/open_interpreter.Dockerfile -t open_interpreter:latest .

  * Before starting the server, ensure to comment out the autogpt section in the open_instruction.yml file.
  
  * Then, start the server and multiple communication agents by running:
  
    .. code-block:: bash

      docker-compose -f dockerfiles/open_instruction.yml up






