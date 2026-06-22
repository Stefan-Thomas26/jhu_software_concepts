"""Module for loading and viewing JSON data files."""

import json
import os


def load_data(file_path):
    """Load and return data from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data


def view_file(file_path):
    """Open a file using the default OS application."""
    os.startfile(file_path)
