import json
import os

def load_data(filePath):

    with open(filePath, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    return data
        
    # Print .json file to the terminal. NOT IDEAL
    # print(json.dumps(data, indent=4))

    # load_data FUNCTION END

def view_file(filePath):

    os.startfile(filePath)
    
    # open_file FUNCTION END
