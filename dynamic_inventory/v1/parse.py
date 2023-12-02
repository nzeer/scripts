import pathlib as p
from dataclasses import dataclass

""" =========================================================
parse files in ./hosts and build inventories based off:
  - ip (configurable)
  - os family
  - major release version 
============================================================="""


@dataclass
class HostInfo:
    """Class for tracking host info"""

    name: str
    ip_list: list
    os_info_list: list

    def fqdn(self) -> str:
        return self.name

    def ips(self) -> list:
        return self.ip_list

    def os_version(self) -> str:
        return self.os_info_list[1]

    def os_family(self) -> str:
        return self.os_info_list[0]


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


def write_inventory(hosts=[], inv_dir=""):
    path = p.Path(inv_dir)
    dir_exists = path.exists()
    host = HostInfo(name="", ip_list=[], os_info_list=[])
    try:
        if not dir_exists:
            path.mkdir()
        else:
            for h in hosts:
                host = HostInfo(name="", ip_list=[], os_info_list=[])
                # content: "{{ ansible_fqdn, ansible_all_ipv4_addresses, [os_distro, os_version] }}"
                # ('localhost-live.maersk.homenet.lan', ['172.16.20.156', '172.16.30.161'], ['Fedora', '39'])
                host = h
                print(host.name)
                print(host.ip_list)
                print(host.os_info_list)
                print(host.os_family)
                print(host.os_version)

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
    print(hosts_loaded)
    # write_inventory(hosts_loaded, inventory_directory)


# Check if the script is run as the main module
if __name__ == "__main__":
    # Call the main function
    main()
