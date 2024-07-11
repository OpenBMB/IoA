Docker Compose Setup
#######################

Customizing the Docker Compose YAML file is essential for setting up the environment to include various agents' Docker containers, along with the configuration of all necessary variables for each container. This setup allows for seamless integration and orchestration of multiple agents and tools within the IoA platform, ensuring they can work together effectively and efficiently. The Docker Compose configuration simplifies the deployment process, providing a centralized way to manage dependencies, environment settings, and network configurations.

Docker Compose Configuration
=====================================
Create your case-specific :code:`your_case.yml` file in the :code:`dockerfiles/compose` directory. For example: :code:`dockerfiles/compose/IOT_Party.yml` 

.. code-block:: yaml

      version: "3"

      service:
      Name:  # e.g. WeizeChen 
         image: Specifies the Docker image to use for this service  # e.g. ioa-client:latest
         build: 
            context: ../../
            dockerfile: dockerfiles/client.Dockerfile
         container_name: the name of the Docker container 
         env_file:
            - .env
         volumes:
            - /var/run/docker.sock:/var/run/docker.sock
            - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/sqlite:/app/database
            - ./volumes/openai_response_log:${OPENAI_RESPONSE_LOG_PATH}
            - ../../configs/client_configs:/app/configs
         environment:
            - OPENAI_API_KEY
            - CUSTOM_CONFIG=agent configuration file path  # e.g. configs/cases/paper_writing/weizechen.yaml
         ports:
            - Maps host_port to container_port, allowing access to the service.  # e.g. 5050:5050
         depends_on:
            - Server
         stdin_open: true
         tty: true

