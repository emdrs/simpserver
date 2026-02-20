import importlib
import sys
import os
from types import ModuleType

sys.path.append(os.getcwd())

user_configs = {
    "DB_CONFIG": {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": ""
    }
}

user_config_module: ModuleType | None = None

try:
    user_config_module = importlib.import_module('config')

    for config in user_configs.keys():
        if hasattr(user_config_module, config):
            user_configs[config] = getattr(user_config_module, config)
except:
    user_configs = None

