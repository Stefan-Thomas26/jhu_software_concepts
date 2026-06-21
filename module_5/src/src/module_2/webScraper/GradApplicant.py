from dataclasses import dataclass, asdict

@dataclass
class GradApplicant:
    applicantNumber: int = None
    university: str = None
    program: str = None
    degreeType: str = None
    datePosted: str = None
    status: str = None
    statusDate: str = None
    semester: str = None
    citizenship: str = None
    gpa: float = None
    gre: float = None
    gre_v: float = None
    gre_aw: float = None
    comment: str = None
    url: str = None