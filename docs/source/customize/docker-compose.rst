#######################
docker-compose
#######################

|

Introduce your OpenAI API Key in the :code:`.env`  file under the :code:`dockerfiles/compose` directory:

.. code-block:: bash

  OPENAI_API_KEY="your_openai_api_key"

.. note::

      The environment variables specified in the :code:`.env` file will be overridden by system environment variables. Please ensure the system environment variables are set correctly.



Docker Compose
=====================================
Create your case-specific :code:`your_case.yml` file in the :code:`dockerfiles/compose` directory. For example: :code:`dockerfiles/compose/IOT_Party.yml` 

.. code-block:: yaml

      version: "3"

      service:
      Name: (ex. Cater)
         image: your_needed_image(ex. IoA-agent:latest)
         build: 
            context: ../../
            dockerfile: your_docker_file(ex. dockerfiles/agent.Dockerfile)
            args: (如果已连接外网，则不需要此参数)
               http_proxy: http://172.27.16.1:7890 
               https_proxy: http://172.27.16.1:7890
         container_name: your_container_name
         env_file:
            - .env
         volumes:
            - /var/run/docker.sock:/var/run/docker.sock
         volumes:
            - OPENAI_API_KEY
            - OPENAI_BASE_URL(如果不需要此参数，请删除)
            - CUSTOM_CONFIG=your_agent.yaml path(ex. agentverse/config/cases/IOT/Caterer.yaml)
         ports:
            - your_host_port:your_container_port(ex. 5051:5050)
         depends_on:
            - Server
            - your_needed_server(ex. IOT-Server)
         stdin_open: true
         tty: true

