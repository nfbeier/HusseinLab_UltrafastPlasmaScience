import json

def load_laser_parameters(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

file = "profiles.json"

laser_parameters = load_laser_parameters(file)

print(laser_parameters["profiles"]['5mJ'])
