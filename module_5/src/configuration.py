"""Module for loading configuration and JSON files."""

import os
import json


def load_json(file_path):
    """Load and return data from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def get_configuration_filepath():
    """Return the path to the local userConfig.json file."""
    config_path = os.path.join(os.path.dirname(__file__), "userConfig.json")
    return config_path


def load_configuration_file():  # pragma: no cover
    """Return username, password, and host from the local config file."""
    config_path = get_configuration_filepath()
    print(config_path)
    if os.path.exists(config_path):
        config_info = load_json(config_path)

        for item in config_info:
            user = item["user"]
            password = item["password"]
            host = item["host"]

        return user, password, host

    return None

if __name__ == "__main__":
    print(os.cpu_count())
