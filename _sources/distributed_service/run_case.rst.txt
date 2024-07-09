########################
Run Case locally
########################

|


.. warning::

   If the service fails to start, try terminating it with Ctrl+C and restart.



Ensure that the MetaAgent Server and IOT Server have started normally on the server, as shown below.


1. The following steps are the same as running the IOT Party scenario. First, create the ReAct image.

   .. code-block:: bash
      
     docker build -f dockerfiles/tool_agents/react.Dockerfile --build-arg http_proxy=http://host.docker.internal:7890 --build-arg https_proxy=http://host.docker.internal:7890 -t react:latest . 
     
|

2. Next, start :code:`test_IOT.yml` using docker-compose.

   .. code-block:: bash

     docker-compose -f dockerfiles/compose/test_IOT.yml up --build

|

3. After starting, execute a command in another command-line window, which will initiate a goal.

   .. code-block:: bash

     python tests/test_IOT_party.py 

