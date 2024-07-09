IoA & IoT Simulation
#######################

|

IOT Party: In an IoT scenario, five agents team up for communication and collaboration to prepare for a party based on a guest information list. These agents are HostAssistant, CatererAssistant, EntertainmentAssistant, EnvironmentAssistant, and DrinkerAssistant. Among them, CatererAssistant, EntertainmentAssistant, EnvironmentAssistant, and DrinkerAssistant are four agents utilizing a ReAct agent's communication layer to operate various smart home tools for party preparation. Here is how to start and use it.



Docker Execution
===========================
* First, create a ReAct Agent image. The http_proxy is optional and is used to employ your machine's proxy when building the Docker container, as some packages require access to blocked websites. If you are not using clash on your computer, replace the 7890 port with your proxy software's port. If you are already outside the firewall, remove this parameter.

  .. code-block:: bash

    docker build -f dockerfiles/tool_agents/react.Dockerfile --build-arg http_proxy=http://host.docker.internal:7890 --build-arg https_proxy=http://host.docker.internal:7890 -t react:latest .  

|

* Start the containers specified in the docker-compose configuration file.

  .. code-block:: bash

    docker-compose -f dockerfiles/compose/IOT_Party.yml up --build

|

* After starting, execute a command in another command-line window, which will initiate a goal.

  .. code-block:: bash

    python tests/test_IOT_party.py 