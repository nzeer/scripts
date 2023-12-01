import pathlib as p

# parse files in ./hosts and build inventories based off:
#   - ip (configurable)
#   - os family


# Define a function to load host data tuple from a file
def load_host(file):
    host_info_tuple = ""
    try:
        path = p.Path(file)
        if not path.exists():
            raise RuntimeError("file does not exist.")
        else:
            # Open the file and read the tuple
            host_info_tuple = open(
                file,
            ).readlines()
    except OSError as e:
        print(e.strerror)
    return host_info_tuple


def load_hosts(directory):
    hosts_loaded = False
    try:
        path = p.Path(directory)
        if not path.exists():
            raise RuntimeError("directory does not exist.")
        else:
            for h in [f for f in path.iterdir() if f.is_file()]:
                load_host(h)
            hosts_loaded = True
    except OSError as e:
        pass
    return hosts_loaded


def write_inventory(hosts={}, file=""):
    path = p.Path(file)
    file_exists = path.exists()
    iplist = []
    try:
        if not file_exists:
            path.mkdir()
            path.touch()
        else:
            pass
        with open(file, "w") as f:
            # Write the INI data to the file
            for h in hosts:
                f.write("\n[%s]\n" % h["name"])
                f.write("%s\n" % h["ip"])
            f.write("\n[devices]\n")
            for ip in iplist:
                f.write("%s\n" % ip)  #   - os major
    except OSError as e:
        print("there was a problem with creating file or path: ", e.strerror)


# Define a main function
def main():
    # Get the JSON file name from the user input or use the default
    # json_file = input("Enter the JSON file name: ") or "./hosts.json"
    # Get the INI file name from the user input or use the default
    # ini_file = input("Enter the INI file name: ") or "./hosts.ini"
    # Call the load_json function and get the JSON data
    # json_data = load_json(json_file)
    # Call the write_ini function and write the INI data to the file
    hosts_info_directory = "./hosts"
    inventory_directory = "./inventories"

    # load all host info from text files (tuples) in a given directory
    load_hosts(hosts_info_directory)

    write_inventory(inventory_directory)
    # Print a success message
    # print(f"Successfully converted {json_file} to {ini_file}")


# Check if the script is run as the main module
if __name__ == "__main__":
    # Call the main function
    main()
