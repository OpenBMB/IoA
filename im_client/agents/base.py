import os
from common.types.llm import LLMResult
import docker


class AgentAdapter:
    def reset(self):
        pass

    async def run(self, task_desc: str):
        pass

    async def step(self):
        pass

    async def create_task(self, task_desc: str):
        pass

    async def add_to_memory(self, message: LLMResult):
        pass

    async def get_memory(self) -> list[LLMResult]:
        pass

    async def shutdown(self):
        pass

    @classmethod
    def create(cls, config: dict | None):
        if config is None:
            return None
        agent_type = config.get("agent_type", None)
        match agent_type:
            case "ReAct":
                from agents import ReActAgent

                client = docker.from_env()
                exist_container = client.containers.list(all=True, filters={"name": config["container_name"]})
                if len(exist_container) > 0:
                    exist_container[0].remove(force=True)
                docker_container = client.containers.run(
                    config["image_name"],
                    name=config["container_name"],
                    detach=True,
                    remove=False,
                    environment=[
                        f"OPENAI_API_KEY={os.environ.get('OPENAI_API_KEY')}",
                        f"OPENAI_BASE_URL={os.environ.get('OPENAI_BASE_URL')}",
                        f"BING_API_KEY={os.environ.get('BING_API_KEY')}",
                        f"AGENT_NAME={config.get('agent_name', '')}",
                        f"AGENT_DESC={config.get('desc', '')}",
                        f"AGENT_MODEL={config.get('model', '')}",
                        f"MAX_NUM_STEPS={config.get('max_num_steps', 20)}",
                        f"TOOLS_CONFIG={config.get('tools_config')}",
                        f"OPENAI_API_BASE={os.environ.get('OPENAI_API_BASE', '')}",
                        f"CUPS_SERVER={os.environ.get('CUPS_SERVER', '')}",
                        f"PRINTER_NAME={os.environ.get('PRINTER_NAME', '')}",
                        f"PERSIST_DIR={config.get('rag').get('persist_dir', '')}",
                        f"CHUNK_SIZE={config.get('rag').get('chunk_size', '')}",
                        f"RAG_LLM_MODEL={config.get('rag').get('llm_model', '')}",
                        f"RAG_LLM_TEMPERATURE={config.get('rag').get('llm_temperature', '')}",
                        f"SIMILARITY_TOP_K={config.get('rag').get('similarity_top_k', '')}",
                        f"RAG_DATA={config.get('rag').get('data', '')}",
                        f"MI_USER={os.environ.get('MI_USER', '')}",
                        f"MI_PASSWORD={os.environ.get('MI_PASSWORD', '')}",
                    ],
                    tty=True,
                    stdin_open=True,
                    network="agent_network",
                    privileged=True,
                    # ports={"7070/tcp": config.get("port")},
                )
                return ReActAgent(docker_container, config["agent_name"])
            case "OpenInterpreter":
                from agents import OpenInterpreterAgent

                client = docker.from_env()
                exist_container = client.containers.list(all=True, filters={"name": config["container_name"]})
                if len(exist_container) > 0:
                    exist_container[0].remove(force=True)
                docker_container = client.containers.run(
                    config["image_name"],
                    name=config["container_name"],
                    detach=True,
                    remove=True,
                    environment=[
                        f"OPENAI_API_KEY={os.environ.get('OPENAI_API_KEY')}",
                        f"OPENAI_BASE_URL={os.environ.get('OPENAI_BASE_URL')}",
                        f"OPENAI_API_BASE={os.environ.get('OPENAI_API_BASE', '')}",
                    ],
                    tty=True,
                    stdin_open=True,
                    network="agent_network",
                    privileged=True,
                    ports={"7070/tcp": config.get("port")},
                )
                return OpenInterpreterAgent(
                    docker_container,
                    "OpenInterpreter Agent",
                )

            case "AutoGPT":
                from agents import AutoGPTAgent

                client = docker.from_env()
                exist_container = client.containers.list(all=True, filters={"name": config["container_name"]})
                if len(exist_container) > 0:
                    exist_container[0].remove(force=True)
                docker_container = client.containers.run(
                    config["image_name"],
                    command="serve",
                    name=config["container_name"],
                    detach=True,
                    remove=True,
                    environment=[
                        f"OPENAI_API_KEY={os.environ.get('OPENAI_API_KEY')}",
                        f"OPENAI_API_BASE_URL={os.environ.get('OPENAI_API_BASE_URL')}",
                        f"OPENAI_API_BASE={os.environ.get('OPENAI_API_BASE', '')}",
                        f"OPENAI_BASE_URL={os.environ.get('OPENAI_BASE_URL', '')}",
                        f"USE_WEB_BROWSER={os.environ.get('USE_WEB_BROWSER', '')}",
                        f"HEADLESS_BROWSER={os.environ.get('HEADLESS_BROWSER', '')}",
                        f"DISABLED_COMMANDS={os.environ.get('DISABLED_COMMANDS', '')}",
                        f"GOOGLE_API_KEY={os.environ.get('GOOGLE_API_KEY', '')}",
                        f"EXECUTE_LOCAL_COMMANDS={os.environ.get('EXECUTE_LOCAL_COMMANDS', '')}",
                        f"GOOGLE_CUSTOM_SEARCH_ENGINE_ID={os.environ.get('GOOGLE_CUSTOM_SEARCH_ENGINE_ID', '')}",
                        f"SMART_LLM={os.environ.get('SMART_LLM', '')}",
                        f"FAST_LLM={os.environ.get('FAST_LLM', '')}",
                    ],
                    tty=True,
                    stdin_open=True,
                    network="agent_network",
                    privileged=True,
                    ports={"8000/tcp": config.get("port")},
                )

                return AutoGPTAgent(docker_container, config["agent_name"])
