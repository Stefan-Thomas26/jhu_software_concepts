import json
def _load_json(filePath):

    with open(filePath, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    return data