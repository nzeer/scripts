import os
import pathlib as p

from libhostinfo import HostInfo
from libinventoryinfo import Inventory, InventoryEntry

# print debug messages to the console at runtime
debug = True

""" =========================================================
parse files in ./hosts and build inventories based off:
  - ip (configurable)
  - os family
  - major release version 
============================================================="""


""" =========================================================
load host data into HostInfo instance

Return Type: HostInfo
============================================================="""
def load_host(file):
    current_host = HostInfo("", [], [], "", "")
    if debug: print("reading file:", file)
    try:
        path = p.Path(file)
        if not path.exists():
            raise RuntimeError("file does not exist.")
        else:
            # Open the file and read the tuple
            # current_host.name, current_host.ip_list, current_host.os_info_list =
            res = eval(
                open(
                    file,
                ).readline()
            )
            if debug: print("loading host: ", res)
            return HostInfo(res[0], res[1], res[2], res[2][0], res[2][1])
    except OSError as e:
        print(e.strerror)
    return current_host

""" =========================================================
Load all hosts in a given directory

ReturnType: list of HostInfo objects
============================================================="""
def load_hosts(directory):
    if debug: print("Using directory: ", directory)
    loaded_hosts = []
    host = HostInfo("", [], [], "", "")
    try:
        path = p.Path(directory)
        if not path.exists():
            raise RuntimeError("directory does not exist.")
        else:
            for h in [f for f in path.iterdir() if f.is_file()]:
                host = HostInfo("", [], [], "", "")
                host = load_host(h)
                loaded_hosts.append(host)
                host = None
    except OSError as e:
        pass
    return loaded_hosts

""" =========================================================
Write out inventory files broken out by
  - Network (subnet)
  - Os family/release major version
TODO: create a world file
TODO: variables per inventory
TODO: Server groupings (custom config options)
============================================================="""
def write_inventory(hosts=[], inv_dir=""):
    if debug:print("Using directory: ", inv_dir)
    inventory_out = Inventory(
        items=[],
        list_nipr=[],
        list_dev=[],
        list_stand_alone=[],
        list_unknown=[],
        list_formatted_host_entries=[],
    )
    # set our path and flag if it exists
    path = p.Path(inv_dir)
    dir_exists = path.exists()
    try:
        # create our output directory
        if not dir_exists:
            path.mkdir()
        # iterate through all hosts
        for h in hosts:
            # instantiate blank host
            host = HostInfo(
                name="",
                ip_list=[],
                os_info_list=[],
                os_distro="",
                os_distro_version_major="",
            )
            # instantiate blank inventory entry
            inventory_entry = InventoryEntry(
                nipr_ip="",
                dev_ip="",
                stand_alone_ip="",
                unknown_subnet_ip="",
                hostname="",
                ip_list=[],
                distro="",
                release="",
            )
            # content: "{{ ansible_fqdn, ansible_all_ipv4_addresses, [os_distro, os_version] }}"
            # ('localhost-live.maersk.homenet.lan', ['172.16.20.156', '172.16.30.161'], ['Fedora', '39'])
            host = h
            # add host to inventory entry
            inventory_entry.add_host(h)
            # store inventory entry in inventory
            inventory_out.get_inventory_entries().append(inventory_entry)
            # add ip to appropriate ip list
            inventory_out.add_ip(inventory_entry.get_ip_list())
            if debug: print(inventory_out)
            if debug: print(inventory_entry)
            # cleanup and prepare for the next iteration
            host = None
            inventory_entry = None
        ientry_list = inventory_out.get_inventory_entries()
        for inv in ientry_list:
            host = HostInfo(
                name="",
                ip_list=[],
                os_info_list=[],
                os_distro_version_major="",
                os_distro="",
            )
            # host = inv
            os_path = os.path.join(inv_dir, inv.get_distro())
            path = p.Path(os_path)
            if not os.path.exists(os_path):
                path = p.Path(os_path)
                path.mkdir()
            release_path = os.path.join(os_path, inv.get_release())
            if not os.path.exists(release_path):
                path = p.Path(release_path)
                path.mkdir()
                inventory_path = os.path.join(release_path, "inventory")
                path = p.Path(inventory_path)
                path.touch()
        if debug: print(inventory_out.get_inventory_entries())
        if debug: print(inventory_out.print_ips())

        # for entry in inventory.list_inventory_entries:
        # os_dir = p.Path(inv_dir+"/"+ entry.)
        # pass
        # with open(file, "w") as f:
        # Write the INI data to the file
        #    for h in hosts:
        #        f.write("\n[%s]\n" % h["name"])
        #        f.write("%s\n" % h["ip"])
        #    f.write("\n[devices]\n")
        #    for ip in iplist:
        #        f.write("%s\n" % ip)  #   - os major
    except OSError as e:
        print("there was a problem")

""" =========================================================
Define an entry point
============================================================="""
def main():
    hosts_info_directory = "./hosts"
    inventory_directory = "./inventories"

    # load all host info from text files (tuples) in a given directory
    hosts_loaded = load_hosts(hosts_info_directory)
    # for h in hosts_loaded:
    #    print(h)
    write_inventory(hosts_loaded, inventory_directory)


# Check if the script is run as the main module
if __name__ == "__main__":
    # Call the main function
    main()
