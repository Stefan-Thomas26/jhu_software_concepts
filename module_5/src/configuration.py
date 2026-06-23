"""Module for loading configuration and JSON files."""

import os
import json


def load_json(file_path):
    """Load and return data from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data

def load_configuration_file():  # pragma: no cover
    """Return username, password, and host from environment variables."""
    user = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")
    host = os.environ.get("DB_HOST", "localhost")

    if not all([user, password, host]):
        raise ValueError(
            "Missing required environment variables: DB_USER, DB_PASSWORD, DB_HOST"
        )

    return user, password, host

if __name__ == "__main__":
    print(os.cpu_count())
