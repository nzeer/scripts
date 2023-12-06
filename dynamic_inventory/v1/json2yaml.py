# Import the json and configparser modules
import configparser
import json
import pathlib as p

debug = False

json_file = "./hosts.json"
inventory_file = "./inventory"
hosts_directory = "./hosts"

# Define a function to load JSON data from a file
def load_json(file):
    if debug: print("using file: ", file)
    # Open the file in read mode
    with open(file, "r") as f:
        # Load the JSON data and return it
        data = json.load(f)
        return data


# Define a function to write data to a file
def write_inventory(data, file):
    myfindings = {}
    devices = []
    iplist = []
    # Create a ConfigParser object
    config = configparser.ConfigParser()
    # Loop through the data
    for key, value in data.items():
        # Check if the key is _meta
        if key == "_meta":
            # Skip this key as it is not needed for the hosts file
            myfindings = list(data.items())[0][1]["hostvars"]
            for k in myfindings:
                curdict = myfindings[k]
                # only configure for host entry if there's a host name to work with.
                if curdict["ip"] != curdict["name"]:
                    devices.append(curdict)
                    #if debug: print(curdict)
                iplist.append(curdict["ip"])
            continue
    if debug: print("\nfindings: ", myfindings)
    with open(file, "w") as f:
        # Write the data to the file
        for d in devices:
            # write out individual host entries for anything with a host name.
            f.write("\n[%s]\n" % d["name"])
            f.write("%s\n" % d["ip"])
        # write out all ip's to their own section
        f.write("\n[devices]\n")
        for entry in iplist:
            f.write("%s\n" % entry)
    # create hosts directory
    path = p.Path(hosts_directory)
    if not path.exists(): path.mkdir()


# Define a main function
def main():
    # Get the JSON file name from the user input or use the default
    # json_file = input("Enter the JSON file name: ") or "./hosts.json"
    # Get the INI file name from the user input or use the default
    # ini_file = input("Enter the INI file name: ") or "./hosts.ini"
    # Call the load_json function and get the JSON data
    json_data = load_json(json_file)
    # Call the write_ini function and write the INI data to the file
    write_inventory(json_data, inventory_file)
    
    # Print a success message
    if debug: print(f"Successfully converted {json_file} to {inventory_file}")


# Check if the script is run as the main module
if __name__ == "__main__":
    # Call the main function
    main()
