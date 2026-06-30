"""Module defining the GradApplicant dataclass for storing applicant records."""

from dataclasses import dataclass


@dataclass
class GradApplicant:
    """Dataclass representing a graduate school applicant and their stats."""

    applicant_number: int = None
    university: str = None
    program: str = None
    degree_type: str = None
    date_posted: str = None
    status: str = None
    status_date: str = None
    semester: str = None
    citizenship: str = None
    gpa: float = None
    gre: float = None
    gre_v: float = None
    gre_aw: float = None
    comment: str = None
    url: str = None
