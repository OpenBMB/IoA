IoA Installation
#############################

🚀 Quick Start
=============================================

Get IoA up and running in just a few steps:

1. 📋 Prerequisites
--------------------
* Make sure you have Docker installed on your local environment. If Docker is not installed, for download details, please visit the `Docker official website <https://docs.docker.com/desktop/>`_ .

2. 🛳️ Clone the Repository
---------------------------

.. code-block:: bash

   git clone git@github.com:OpenBMB/IoA.git
   cd IoA

3. 🏗️ Build Docker Images
--------------------------

Core Components
^^^^^^^^^^^^^^^

You can directly pull the pre-built docker images from docker hub:

.. code-block:: bash

   # Server
   docker pull weize/ioa-server:latest

   # Client
   docker pull weize/ioa-client:latest

   # Server Frontend
   docker pull weize/ioa-server-frontend:latest

   # Rename the images
   docker tag weize/ioa-server:latest ioa-server:latest
   docker tag weize/ioa-client:latest ioa-client:latest
   docker tag weize/ioa-server-frontend:latest ioa-server-frontend:latest

Or you can build from source

.. code-block:: bash

   # Server
   docker build -f dockerfiles/server.Dockerfile -t ioa-server:latest .

   # Client
   docker build -f dockerfiles/client.Dockerfile -t ioa-client:latest .

   # Server Frontend
   docker build -f dockerfiles/server_frontend.Dockerfile -t ioa-server-frontend:latest .

Agent Images (Build as needed)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # ReAct Agent
   docker pull weize/react-agent:latest
   docker tag weize/react-agent:latest react-agent:latest

   # AutoGPT (we have fixed some bugs in AutoGPT's original docker image)
   docker pull weize/autogpt:latest
   docker tag weize/autogpt:latest autogpt:latest

   # Open Interpreter
   docker pull weize/open-interpreter:latest
   docker tag weize/open-interpreter:latest open-interpreter:latest

Or you can build from source

.. code-block:: bash

   # ReAct Agent
   docker build -f dockerfiles/tool_agents/react.Dockerfile -t react-agent:latest .   

   # AutoGPT (we have fixed some bugs in AutoGPT's original docker image)
   docker build -f dockerfiles/tool_agents/autogpt.Dockerfile -t autogpt:latest .   

   # Open Interpreter
   docker build -f dockerfiles/tool_agents/open_interpreter.Dockerfile -t open-interpreter:latest .

4. 🌐 Launch Milvus Service
------------------------------
.. code-block:: bash

   docker network create agent_network
   docker-compose -f dockerfiles/compose/milvus.yaml up


5. 🎬 Start IoA
----------------

.. code-block:: bash

   cd dockerfiles/compose/
   cp .env_template .env

In :code:`.env`, fill in your OpenAI API key and other optional environment variables. Then for a quick demo with AutoGPT and Open Interpreter:

.. code-block:: bash

   cd ../../
   docker-compose -f dockerfiles/compose/open_instruction.yaml up

And you will set up your own small-scale Internet of Agents with AutoGPT and Open Interpreter!

6. 🧪 Test It Out
---------------------
You can use the following script to test IoA on our Open Instruction dataset.

.. code-block:: bash

   python scripts/open_instruction/test_open_instruction.py

Or simply send a post request like:

.. code-block:: python

   import requests

   goal = "I want to know the annual revenue of Microsoft from 2014 to 2020. Please generate a figure in text format showing the trend of the annual revenue, and give me a analysis report."

   response = requests.post(
    "http://127.0.0.1:5050/launch_goal",
    json={
        "goal": goal,
        "max_turns": 20,
        "team_member_names": ["AutoGPT", "Open Interpreter"],   # When it is left "None", the agent will decide whether to form a team autonomously
    },
   )

   print(response)
   
