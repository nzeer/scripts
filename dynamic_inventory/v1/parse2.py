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
        dict_unknown_subnet={},
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
            if debug: print("inventory: ", inventory_out)
            if debug: print("inventory entry: ", inventory_entry)
            # cleanup and prepare for the next iteration
            host = None
            inventory_entry = None
        
        # iterate through inventory entries
        for inv_entry in inventory_out.get_inventory_entries():
            if debug: print("parsing inventory entry: ", inv_entry)
            host = HostInfo(
                name="",
                ip_list=[],
                os_info_list=[],
                os_distro_version_major="",
                os_distro="",
            )
            if debug: print("inventory obj: ", inv_entry)
            # create distro/release directory structure, returning path to distro/release inventory file
            inv_path = create_directory_structure(inv_dir, inv_entry.get_distro(), inv_entry.get_release())

            # ignore anything but stand alone ip's since we dual home everything
            write_stand_alone(inv_path, inv_entry.get_host_name(), inv_entry.get_stand_alone_ip())
            
        if debug: print(inventory_out.get_inventory_entries())
        if debug: print(inventory_out.print_ips())

        # write ./inventories/inventory file, broken up across known subnets
        #inventory_file = os.path.join(inv_dir, "inventory")
        write_subnets(os.path.join(inv_dir, "inventory"), inventory_out.get_unknown_ip_list(), inventory_out.get_stand_alone_ip_list(), inventory_out.get_nipr_ip_list(), inventory_out.get_dev_ip_list())
    except OSError as e:
        print("there was a problem")

def write_subnets(inv_file, list_unknown, list_sa, list_nipr, list_dev):
    # write out all hosts by subnet in top level inventory file
    with open(inv_file, "w") as f:
        if list_unknown:
            if debug: print("unknown ips: ", list_unknown)
            f.write("\n[unknown]\n")
            for ip in list_unknown:
                f.write("%s\n" % ip)
        
        if list_nipr:
            if debug: print("nipr ips: ", list_nipr)
            f.write("\n[nipr]\n")
            for ip in list_nipr:
                f.write("%s\n" % ip)
        
        if list_dev:
            if debug: print("dev ips: ", list_dev)
            f.write("\n[dev]\n")
            for ip in list_dev:
                f.write("%s\n" % ip)

        if list_sa:
            if debug: print("standalone ips: ", list_sa)
            f.write("\n[standalone]\n")
            for ip in list_sa:
                f.write("%s\n" % ip)

def create_directory_structure(inventory_directory, distro, release) -> str:
    os_path = os.path.join(inventory_directory, distro)
    path = p.Path(os_path)
    if not os.path.exists(os_path):
        path = p.Path(os_path)
        path.mkdir()
    release_path = os.path.join(os_path, release)
    inventory_path = os.path.join(release_path, "inventory")
    if not os.path.exists(release_path):
        path = p.Path(release_path)
        path.mkdir()
        path = p.Path(inventory_path)
        path.touch()
    return inventory_path

def write_stand_alone(inv_path, host_name, ip):
    if ip:
        file1 = open(inv_path, "a")  # append mode
        file1.write("\n[%s]\n" % host_name)
        file1.write("%s\n" % ip)
        file1.close()
    
""" =========================================================
Define an entry point
============================================================="""
def main():
    hosts_info_directory = "./hosts"
    inventory_directory = "./inventories"

    # load all host info from text files (tuples) in a given directory
    hosts_loaded = load_hosts(hosts_info_directory)
    write_inventory(hosts_loaded, inventory_directory)


# Check if the script is run as the main module
if __name__ == "__main__":
    # Call the main function
    main()
