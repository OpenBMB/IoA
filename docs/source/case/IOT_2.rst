IoA & IoT Real-World
#######################

|

IOT Real Device: In the IoT real device scenario, real Xiaomi smart home devices are accessed through the miio protocol. This includes the Mijia LED Desk Lamp 1S Enhanced Edition (Black), Redmi Projector 2,Mijia Smart DC Standing Fan 1X, Xiaomi Smart Air Purifier 4 Lite, Mijia Smart Hot and Cold Water Dispenser, MI AI Speaker (2nd Gen), and Mijia Smart Anti-bacterial Humidifier 2. Agents enable interconnectivity and communication between devices, coordinating various smart home appliances to create an intelligent and comfortable living experience.

Docker Execution
===========================
* First, create a ReAct Agent image. The http_proxy is optional and is for using your local machine's proxy when building the Docker container, as some packages require bypassing internet restrictions. If you are not using clash on your computer, replace the 7890 port with your proxy software's port. If you are already outside the network restrictions, remove this parameter.

  .. code-block:: bash

    docker build -f dockerfiles/tool_agents/react.Dockerfile --build-arg http_proxy=http://host.docker.internal:7890 --build-arg https_proxy=http://host.docker.internal:7890 -t react:latest . 

|

* Start the containers specified in the docker-compose configuration file.

  .. code-block:: bash

     docker-compose -f dockerfiles/compose/IOT_Party.yml up --build

|

* After starting, execute a command in another command-line window, which will initiate a goal.

  .. code-block:: bash

    python tests/test_IOT_real.py