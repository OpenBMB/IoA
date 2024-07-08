import yaml
import os
from .log import logger


def _update_config(default, user):
    for key, value in user.items():
        if isinstance(value, dict):
            default[key] = _update_config(default.get(key, {}), value)
        else:
            default[key] = value
    return default


def update_custom_config(config):
    if custom_config_path := os.getenv("CUSTOM_CONFIG", ""):
        logger.info("Loading custom config from %s" % custom_config_path)
        custom_config: dict = yaml.safe_load(open(custom_config_path))

        _update_config(config, custom_config)


try:
    global_config = yaml.safe_load(open(os.path.join("configs", "default_config.yaml")))
except FileNotFoundError:
    logger.warn(
        "No default config file found, using empty config as the default config. If you want to use a default config file, please make sure it is in the 'configs' folder and named 'default_config.yaml'"
    )
    global_config = {}
update_custom_config(global_config)
