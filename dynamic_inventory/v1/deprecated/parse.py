import os
import pathlib as p

from HostInfo import HostInfo
from InventoryInfo import Inventory, InventoryEntry

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
    current_host = HostInfo("", [], [])
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
            return HostInfo(res[0], res[1], res[2])
    except OSError as e:
        print(e.strerror)
    return current_host


""" =========================================================
Load all hosts in a given directory

ReturnType: list of HostInfo objects
============================================================="""


def load_hosts(directory):
    loaded_hosts = []
    host = HostInfo("", [], [])
    try:
        path = p.Path(directory)
        if not path.exists():
            raise RuntimeError("directory does not exist.")
        else:
            for h in [f for f in path.iterdir() if f.is_file()]:
                host = HostInfo("", [], [])
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

"""ip_nipr_dict: dict
    ip_stand_alone_dict: dict
    ip_dev_dict: dict
    nipr_ip_list: list
    dev_ip_list: list
    stand_alone_ip_list: list
    unknown_subnet_ip_list: list
    hostname: str
    os_distro: str
    os_release: str"""


def write_inventory(hosts=[], inv_dir=""):
    """inventory_entry = InventoryEntry(
        nipr_ip_list=[],
        dev_ip_list=[],
        stand_alone_ip_list=[],
        unknown_subnet_ip_list=[],
        hostname="",
        os_distro="",
        os_release="",
    )"""
    inventory = Inventory(
        items=[],
        list_nipr=[],
        list_dev=[],
        list_stand_alone=[],
        list_unknown=[],
        list_entries=[],
    )
    path = p.Path(inv_dir)
    dir_exists = path.exists()
    try:
        if not dir_exists:
            path.mkdir()
        for h in hosts:
            host = HostInfo(name="", ip_list=[], os_info_list=[])
            inventory_entry = InventoryEntry(
                nipr_ip_list=[],
                dev_ip_list=[],
                stand_alone_ip_list=[],
                unknown_subnet_ip_list=[],
                hostname="",
                os_distro="",
                os_release="",
                ip_list=[],
            )
            # content: "{{ ansible_fqdn, ansible_all_ipv4_addresses, [os_distro, os_version] }}"
            # ('localhost-live.maersk.homenet.lan', ['172.16.20.156', '172.16.30.161'], ['Fedora', '39'])
            host = h
            inventory_entry.add_host(h)
            inventory.items.append(h)
            # inventory.items.append(inventory_entry)
            inventory.add_ip(h.ip_list)
            host = None
            inventory_entry = None
        # print(inventory)
        for inv in inventory.items:
            host = HostInfo(name="", ip_list=[], os_info_list=[])
            host = inv
            os_path = os.path.join(inv_dir, host.distro())
            path = p.Path(os_path)
            if not os.path.exists(os_path):
                path = p.Path(os_path)
                path.mkdir()
            release_path = os.path.join(os_path, host.version())
            if not os.path.exists(release_path):
                path = p.Path(release_path)
                path.mkdir()
                inventory_path = os.path.join(release_path, "inventory")
                path = p.Path(inventory_path)
                path.touch()
            print(host.ip_list)

        for entry in inventory.list_entries:
            # os_dir = p.Path(inv_dir+"/"+ entry.)
            pass
        # with open(file, "w") as f:
        # Write the INI data to the file
        #    for h in hosts:
        #        f.write("\n[%s]\n" % h["name"])
        #        f.write("%s\n" % h["ip"])
        #    f.write("\n[devices]\n")
        #    for ip in iplist:
        #        f.write("%s\n" % ip)  #   - os major
    except OSError as e:
        print("there was a problem with creating file or path: ", file)


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
