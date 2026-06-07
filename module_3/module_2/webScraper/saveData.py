from dataclasses import asdict, is_dataclass
import json

# =============================
# Save Grad School applicant 
# data as a .json file 
# =============================
def save_data(allGradApplicants, filePath):

    if allGradApplicants and is_dataclass(allGradApplicants[0]):
        allGradApplicants = [asdict(student) for student in allGradApplicants]

    with open(filePath, "w", encoding="utf-8") as f:
        json.dump(allGradApplicants, f, indent=4)
    
    print("")
    print("::::::::::::::::::::::")
    print("!!! ALL DATA SAVED !!!")
    print("::::::::::::::::::::::")
    # save_data FUNCTION END
