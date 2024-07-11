.. Running IoA on Different Devices
.. --------------------------------
.. This guide explains how to configure the IoA framework to run on distributed devices.

.. 🗄️ Server
.. +++++++++++++++++++++++
.. 1. Open TCP & UDP ports
..    Open two ports for network access. By default, you should open port 7788 for the server (denoted as <SERVER_PORT>), and 80 for the webpage frontend (denoted as <FRONTEND_PORT>), but in case where these ports are occupied on your server, you can open other ports.

.. 2. Pull or build necessary docker images:

.. .. code-block:: bash

..    # Server
..    docker pull weize/ioa-server:latest

..    # Server Frontend
..    docker pull weize/ioa-server-frontend:latest

..    # Rename the images
..    docker tag weize/ioa-server:latest ioa-server:latest
..    docker tag weize/ioa-server-frontend:latest ioa-server-frontend:latest

.. 3. Launch Milvus service:

.. .. code-block:: bash

..    docker-compose -f dockerfiles/compose/milvus.yaml up

.. 4. Launch IoA's server:

.. .. code-block:: bash

..    docker-compose -f dockerfiles/compose/server_only.yaml up

.. .. note:: If port `7788` or `80` has already been occupied on your server, revise the port mapping in the yaml file. For example:

..    .. code-block:: yaml

..       Server:
..          ...
..          ports:
..             - <SERVER_PORT>:7788 # Fill <SERVER_PORT> with an opened port on your server
      
..       ...
..       ServerFrontend:
..          ...
..          ports:
..             - <FRONTEND_PORT>:80  # Fill <FRONTEND_PORT> with an opened port on your server

.. You can then access `<SERVER_IP>:<FRONTEND_PORT>` for the server's frontend showing the agents' communication.

.. 💻 Client
.. +++++++++
.. 1. Pull or build necessary docker images:

.. .. code-block:: bash

..    docker pull weize/ioa-client:latest
..    docker tag weize/ioa-client:latest ioa-client:latest

..    # Pull or Build Your Agent Docker, for example, to pull a react agent docker:
..    # docker pull weize/react-agent:latest
..    # docker tag weize/react-agent:latest react-agent:latest 

.. 2. In client's config file, properly config the server:

.. .. code-block:: yaml

..    server:
..       port: <SERVER_PORT>    # e.g., 7788
..       hostname: <SERVER_IP>  # e.g., 43.163.221.23

.. 3. Launch Milvus service:

.. .. code-block:: bash

..    docker-compose -f dockerfiles/compose/milvus.yaml up

.. 4. Launch your client with your agent. 

.. For example, in `configs/client_configs/case/example/bob.yaml` you can replace the `<SERVER_PORT>` and `<SERVER_IP>` with the opened port and ip of your server, and launch an example:

.. .. code-block:: bash

..    docker-compose -f dockerfiles/compose/example.yaml up


.. ❓ Troubleshooting
.. +++++++++++++++++++++++++++++++++++
.. - If connections fail, check firewall settings and ensure ports are correctly forwarded.
.. - Verify that all IP addresses and hostnames are correctly set in the configuration files.
.. - Check network connectivity between devices using ping or traceroute.

.. For additional help, you can raise an issue in our `Github repo <https://github.com/OpenBMB/IoA/issues>`_.






Running IoA on Distributed Devices
==================================

This guide explains how to configure and run the IoA framework across multiple devices.

🗄️ Server Setup
----------------

1. Configure Network Access
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Open two ports on your server:

- :code:`<SERVER_PORT>` (default: 7788) for the IoA server
- :code:`<FRONTEND_PORT>` (default: 80) for the web frontend

.. note:: If the default ports are occupied, choose alternative available ports.

2. Prepare Docker Images
^^^^^^^^^^^^^^^^^^^^^^^^
Pull and rename the necessary images:

.. code-block:: bash

   docker pull weize/ioa-server:latest
   docker pull weize/ioa-server-frontend:latest
   docker tag weize/ioa-server:latest ioa-server:latest
   docker tag weize/ioa-server-frontend:latest ioa-server-frontend:latest

3. Launch Services
^^^^^^^^^^^^^^^^^^
Start the Milvus service:

.. code-block:: bash

   docker-compose -f dockerfiles/compose/milvus.yaml up

Launch the IoA server:

.. code-block:: bash

   docker-compose -f dockerfiles/compose/server_only.yaml up

.. note:: If using custom ports, modify the :code:`server_only.yaml` file:

   .. code-block:: yaml

      Server:
         ports:
            - <SERVER_PORT>:7788
      
      ServerFrontend:
         ports:
            - <FRONTEND_PORT>:80

4. Access the Frontend
^^^^^^^^^^^^^^^^^^^^^^
Open :code:`http://<SERVER_IP>:<FRONTEND_PORT>` in a web browser to view the agents' communication interface.

💻 Client Setup
---------------

1. Prepare Docker Images
^^^^^^^^^^^^^^^^^^^^^^^^
Pull the IoA client image and your chosen agent image:

.. code-block:: bash

   docker pull weize/ioa-client:latest
   docker tag weize/ioa-client:latest ioa-client:latest

   # Example for React agent:
   # docker pull weize/react-agent:latest
   # docker tag weize/react-agent:latest react-agent:latest 

2. Configure Client
^^^^^^^^^^^^^^^^^^^
Update the client's configuration file:

.. code-block:: yaml

   server:
      port: <SERVER_PORT>    # e.g., 7788
      hostname: <SERVER_IP>  # e.g., 43.163.221.23

3. Launch Milvus Service
^^^^^^^^^^^^^^^^^^^^^^^^
Start the Milvus service on the client device:

.. code-block:: bash

   docker-compose -f dockerfiles/compose/milvus.yaml up

4. Launch Client
^^^^^^^^^^^^^^^^
Start your client with the configured agent. For example:

.. code-block:: bash

   docker-compose -f dockerfiles/compose/example.yaml up

.. note:: Ensure you've updated :code:`configs/client_configs/case/example/bob.yaml` with the correct :code:`<SERVER_PORT>` and :code:`<SERVER_IP>`.

❓ Troubleshooting
-------------------

- Verify firewall settings and port forwarding.
- Double-check IP addresses and hostnames in all configuration files.
- Test network connectivity using ping or traceroute.

For further assistance, please `open an issue on our GitHub repository <https://github.com/OpenBMB/IoA/issues>`_.