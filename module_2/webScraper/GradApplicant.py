from dataclasses import dataclass, asdict

@dataclass
class GradApplicant:
    applicantNumber: int = None
    university: str = None
    program: str = None
    degreeType: str = None
    date_posted: str = None
    decision: str = None
    semester: str = None
    citizenship: str = None
    gpa: float = None
    gre_q: int = None
    gre_v: int = None
    gre_aw: float = None
    comment: str = None
    url: str = None