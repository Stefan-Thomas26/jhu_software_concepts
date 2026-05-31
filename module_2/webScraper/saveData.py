from dataclasses import asdict
import json

# =============================
# Save Grad School applicant 
# data as a .json file 
# =============================
def save_data(allGradApplicants, filename):

    allData = [asdict(student) for student in allGradApplicants]

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(allData, f, indent=4)
    
    print("")
    print("::::::::::::::::::::::")
    print("!!! ALL DATA SAVED !!!")
    print("::::::::::::::::::::::")
    # save_data FUNCTION END
