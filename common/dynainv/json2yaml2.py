# ---
# all:
#  children:
#    - ungrouped
# ungrouped:
#  hosts:
#    - unifi.homenet.lan
##
#
#
# Import the json and yaml modules
import json

import yaml


# Define a function to load JSON data from a file
def load_json(file):
    # Open the file in read mode
    with open(file, "r") as f:
        # Load the JSON data and return it
        data = json.load(f)
        return data


# Define a function to write YAML data to a file
def write_yaml(data, file):
    # Open the file in write mode
    with open(file, "w") as f:
        # Write the YAML data to the file
        yaml.dump(data, f, default_flow_style=False)


# Define a function to convert JSON data to YAML data
def convert_json_to_yaml(json_data):
    # Initialize an empty dictionary to store the YAML data
    yaml_data = {}
    # Loop through the JSON data
    for key, value in json_data.items():
        # Check if the key is _meta
        if key == "_meta":
            # Skip this key as it is not needed for the inventory file
            continue
        # Add the key and value to the YAML data
        print("key: ", key)
        print("value: ", value)
        yaml_data[key] = value
    # Return the YAML data
    return yaml_data


# Define a main function
def main():
    # Get the JSON file name from the user input or use the default
    json_file = input("Enter the JSON file name: ") or "./hosts.json"
    # Get the YAML file name from the user input or use the default
    yaml_file = input("Enter the YAML file name: ") or "./hosts.yml"
    # Call the load_json function and get the JSON data
    json_data = load_json(json_file)
    # Call the convert_json_to_yaml function and get the YAML data
    yaml_data = convert_json_to_yaml(json_data)
    # Call the write_yaml function and write the YAML data to the file
    write_yaml(yaml_data, yaml_file)
    # Print a success message
    print(f"Successfully converted {json_file} to {yaml_file}")


# Check if the script is run as the main module
if __name__ == "__main__":
    # Call the main function
    main()
