######################################
Deploying IoA Service
######################################

|


1. First, access the server.

   .. code-block:: bash

     ssh username@ip_address

|

2. Create a folder and clone IoA into it.

   .. code-block:: bash
      
     cd /data 
     mkdir your_file_name
     cd /data/your_file_name
     git clone https://github.com/AgentVerse/IoA.git

|

3. Pull the image required by the IOT Server in the IOT case.

   .. code-block:: bash

     docker pull mlmz/iot:latest

|

4. The :code:`server.yml` in the :code:`dockerfiles/compose` 目录下的directory includes both IoA Server and IOT Server. Use the docker-compose command to start them on the server.

   .. code-block:: bash

     docker-compose -f dockerfiles/composeserver.yml up --build

|

.. tip::

   If you need to deploy other servers, you can modify server.yml as needed.