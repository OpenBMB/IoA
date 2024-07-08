from . import register_observation
import requests
from common.config import global_config


@register_observation("rocobench")
def get_observation() -> str:
    agent_name = global_config["comm"]["name"]
    resp = requests.post(
        "http://host.docker.internal:8900/get_agent_prompt",
        json={"agent_name": agent_name},
    )
    return resp.json()
