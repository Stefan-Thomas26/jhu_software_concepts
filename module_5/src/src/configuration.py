# Python Packages
import os
import json
# My Packages



# Load JSON FILE
def load_json(filePath):

    with open(filePath, "r", encoding="utf-8") as file:
        data = json.load(file)
        
        # Debugging: Print json out in pretty format
        # print(json.dumps(data, indent=4))
    return data


# Get Config file path from local directory
def get_configuration_filepath():
    # Stores credentials locally after first setup s
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), "userConfig.json")
    return CONFIG_PATH



# !!! THE USER NEEDS TO UPDATE THE userConfig.json !!!
def load_configuration_file():# pragma: no cover
    """Returns config dict if saved, else None."""
    
    CONFIG_PATH = get_configuration_filepath()
    print(CONFIG_PATH)
    if os.path.exists(CONFIG_PATH):
        configInfo = load_json(CONFIG_PATH)

        for item in configInfo:
            user = item["user"]
            password = item["password"]
            host = item["host"]
        
        return user, password, host
    
    return None


print(os.cpu_count())