# Import the json and configparser modules
import json
import configparser


# Define a function to load JSON data from a file
def load_json(file):
    # Open the file in read mode
    with open(file, "r") as f:
        # Load the JSON data and return it
        data = json.load(f)
        return data


# Define a function to write INI data to a file
def write_ini(data, file):
    # Create a ConfigParser object
    config = configparser.ConfigParser()
    # Loop through the data
    for key, value in data.items():
        # Check if the key is _meta
        if key == "_meta":
            # Skip this key as it is not needed for the hosts file
            continue
        # Check if the value is a dictionary
        elif isinstance(value, dict):
            # Check if the value has a hosts key
            if "hosts" in value:
                # Join the hosts with spaces
                hosts = " ".join(value["hosts"])
                # Add the key and hosts to the ConfigParser object
                config[key] = {"hosts": hosts}
        # Check if the value is a list
        elif isinstance(value, list):
            # Join the list items with spaces
            items = " ".join(value)
            # Add the key and items to the ConfigParser object
            config[key] = {"children": items}
    # Open the file in write mode
    with open(file, "w") as f:
        # Write the INI data to the file
        config.write(f)


# Define a main function
def main():
    # Get the JSON file name from the user input or use the default
    json_file = input("Enter the JSON file name: ") or "./hosts.json"
    # Get the INI file name from the user input or use the default
    ini_file = input("Enter the INI file name: ") or "./hosts.ini"
    # Call the load_json function and get the JSON data
    json_data = load_json(json_file)
    # Call the write_ini function and write the INI data to the file
    write_ini(json_data, ini_file)
    # Print a success message
    print(f"Successfully converted {json_file} to {ini_file}")


# Check if the script is run as the main module
if __name__ == "__main__":
    # Call the main function
    main()
