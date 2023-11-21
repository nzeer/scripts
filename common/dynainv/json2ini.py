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
        # Check if the value is a list of hosts
        if isinstance(value, list):
            # Join the hosts with spaces
            value = " ".join(value)
        # Add the key and value to the ConfigParser object
        config[key] = {"hosts": value}
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
