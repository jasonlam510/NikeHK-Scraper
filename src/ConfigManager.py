import sys,os
sys.path.append(os.getcwd())
from src.LoggerConfig import *
import json
import os

CONFIG_PATH = './config.json'

logger = logging.getLogger(__name__)

def load_config(config_example: dict = None)-> dict[str : any]:
    """Load and return the configuration file: create if not exists, add missing keys."""

    # Check if the file exists
    if not os.path.exists(CONFIG_PATH):
        # File does not exist, create it with provided keys and default values
        logger.warning(f"{CONFIG_PATH} is not exists.")
        config = config_example
    else:
        # File exists, read its content
        with open(CONFIG_PATH, 'r') as file:
            config = dict(json.load(file))

        # Append missing keys with default values
        if (config_example is not None):
            for key, default_value in config_example.items():
                if (key not in config.keys()):
                    logger.warning(f"{key} is not found in the {CONFIG_PATH}")
                config.setdefault(key, default_value)

    # Save the updated configuration
    with open(CONFIG_PATH, 'w') as file:
        json.dump(config, file, indent=4)

    return config

if __name__ == '__main__':
    SAMPLE_CONFIG = {}

    logger = setup_logging()
    load_config(SAMPLE_CONFIG)



