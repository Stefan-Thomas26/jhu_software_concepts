from dataclasses import asdict, is_dataclass
import json
import os

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




 
# def save_data(new_entries, filename):
#     """
#     Appends new_entries to an existing JSON file rather than overwriting it.
#     Deduplicates by URL so re-running never creates duplicates in the file.
#     On a fresh full scrape the file won't exist yet, so it is created normally.
#     """
 
#     # Load existing entries if the file already exists
#     existing = []
#     if os.path.exists(filename):
#         try:
#             with open(filename, "r", encoding="utf-8") as f:
#                 existing = json.load(f)
#         except json.JSONDecodeError:
#             print(f"Warning: {filename} was malformed — starting fresh.")
#             existing = []
 
#     # Deduplicate by URL before appending
#     existing_urls = {e.get("url") for e in existing if e.get("url")}
#     truly_new     = [e for e in new_entries if e.get("url") not in existing_urls]
 
#     combined = existing + truly_new
 
#     with open(filename, "w", encoding="utf-8") as f:
#         json.dump(combined, f, indent=2)
 
#     print(f"Saved {len(truly_new)} new entries (file total: {len(combined)}) to {filename}.")

#     print("")
#     print("::::::::::::::::::::::")
#     print("!!! ALL DATA SAVED !!!")
#     print("::::::::::::::::::::::")
#     # save_data FUNCTION END