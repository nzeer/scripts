"""=======================================================================

Author: Rob Jackson

Uses a threadpool to scan subnets via bulk loading nmap plugins, 
executed using ansible-inventory  

=========================================================================="""

from multiprocessing import Pool, TimeoutError
import os
import pathlib as p
import shutil
from datetime import datetime

DEBUG = True
#DEBUG = False
#NMAP_DIRECTORY = "./nmap"
#OUTPUT_DIRECTORY = "./json_hosts_data"

#NMAP_DIRECTORY = "/home/rjackson/dynamic_inventory_live/nmap"
#OUTPUT_DIRECTORY = "/home/rjackson/dynamic_inventory_live/json_hosts_data"
NMAP_DIRECTORY = "/home/rjackson/dynamic_inventory_live_dev/nmap"
OUTPUT_DIRECTORY = "/home/rjackson/dynamic_inventory_live_dev/json_hosts_data"


def get_timestamp() -> str:
    return datetime.now().isoformat(sep=" ")


def delete_directory(directory_path):
    try:
        shutil.rmtree(directory_path)
        if DEBUG:
            print("[%s] Deleted directory: %s" % (get_timestamp(), directory_path))
    except OSError as e:
        print("Error: %s : %s" % (directory_path, e.strerror))


def initialize_directory(directory_path):
    path_directory_path = p.Path(directory_path)
    if path_directory_path.exists():
        if DEBUG:
            print("[%s] Found directory: %s" % (get_timestamp(), directory_path))
        delete_directory(directory_path)
    path_directory_path.mkdir()
    if DEBUG:
        print("[%s] Initialized directory: %s" % (get_timestamp(), directory_path))


def scan_subnet(nmap_plugin_file):
    # split filename on -
    # build ansible command below
    subnet = os.path.basename(nmap_plugin_file).split("-")[0]
    if DEBUG:
        print("[%s] Parsing: %s" % (get_timestamp(), nmap_plugin_file))
        print("[%s] Scanning: %s" % (get_timestamp(), subnet))
    # build ansible-inventory command
    ansible_cmd = ( "ansible-inventory -e='%s' -i %s --export --output=%s/%s-hosts.json --list" % ("@/home/rjackson/.ansible-pass/passwd.yml", nmap_plugin_file, OUTPUT_DIRECTORY, subnet) )
    if DEBUG:
        print("[%s] Running: %s" % (get_timestamp(), ansible_cmd))
    # execute ansible-inventory for current plugin
    os.system(ansible_cmd)
    if DEBUG: 
        print("[%s] Finished scanning: %s" % (get_timestamp(), subnet))
    return True


if __name__ == "__main__":
    # set nmap plugin directory path
    path = p.Path(NMAP_DIRECTORY)
    list_plugins = []
    # initialize output directory
    initialize_directory(OUTPUT_DIRECTORY)
    try:
        if not path.exists():
            raise RuntimeError("%s does not exist." % NMAP_DIRECTORY)
        else:
            list_plugins = [f for f in path.iterdir() if f.is_file()]
    except OSError as e:
            pass
    worker_count = len(list_plugins)
    # start worker processes
    if DEBUG: 
        print("[%s] initializing threadpool with %i workers" % (get_timestamp(), worker_count))
    with Pool(processes=worker_count) as pool:
        if DEBUG:
            print("[%s] Bulk Loading %i plugin(s) from: %s" % (get_timestamp(), worker_count, NMAP_DIRECTORY))
        try:
            pool.map(scan_subnet, list_plugins)
        except OSError as e:
            pass

    # exiting the 'with'-block has stopped the pool
    if DEBUG:
        print("[%s] Completed." % get_timestamp())
