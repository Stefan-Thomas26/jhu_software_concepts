"""Module for saving grad school applicant data to a JSON file."""

from dataclasses import asdict, is_dataclass
import json


def save_data(all_grad_applicants, file_path):
    """Save a list of grad school applicants to a JSON file."""
    if all_grad_applicants and is_dataclass(all_grad_applicants[0]):
        all_grad_applicants = [asdict(student) for student in all_grad_applicants]

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(all_grad_applicants, f, indent=4)

    print("")
    print("::::::::::::::::::::::")
    print("!!! ALL DATA SAVED !!!")
    print("::::::::::::::::::::::")
