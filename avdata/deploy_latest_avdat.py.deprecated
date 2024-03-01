'''================================================================================================
Written by: Robert Jackson
Date: 2024-02-18

This script is used to download and process tar files in preparation of deployment.
config['save_directory'] is the directory where the latest tar file is saved.
config['cache_directory'] is the directory where the tar files are downloaded.
config['tar_files_url'] is the URL of the tar files.

The script performs the following steps:
1. Initialize the directories.
2. Find tar files.
3. Find the latest tar file.
4. Move the latest tar file to the save directory.

Set DEBUG = True to print debug information.
================================================================================================'''

from urllib.request import urlretrieve
from bs4 import BeautifulSoup
import requests
import os
import shutil
from datetime import datetime
import subprocess

DEBUG = True

GLOBAL_CONFIG = {
    'save_directory': "./dat_file",
    'cache_directory': "./.cache",
    'tmp_directory': "./.tmp",
    'avdat_version_file': "latest_avdat.txt",
    'last_avdat_version': '0000',
    'tar_files_url': "https://update.nai.com/products/datfiles/4.x/",
}

'''GLOBAL_ADDITIONAL_CMDS = {
    'avdat_prep_playbook': "/bin/bash ./setup.sh",
    'avdat_playbook_execute': "ansible-playbook -e='@/home/rjackson/.ansible-pass/passwd.yml' /home/rjackson/playbooks/deploy-avdat.yaml",
}'''

GLOBAL_ADDITIONAL_CMDS = {
    'avdat_prep_playbook': "/bin/bash ./test.sh 1234",
    'avdat_playbook_execute': "/bin/bash ./test.sh 23456",
}

GLOBAL_LIST_SYSTEM_DIRECTORIES = [
    "/",
    "/bin",
    "/boot",
    "/dev",
    "/etc",
    "/home",
    "/lib",
    "/lib64",
    "/media",
    "/mnt",
    "/opt",
    "/proc",
    "/root",
    "/run",
    "/sbin",
    "/srv",
    "/sys",
    "/tmp",
    "/usr",
    "/var",
]

def get_timestamp() -> str:
    """
    Returns the current timestamp in ISO 8601 format.

    :return: The current timestamp as a string.
    """
    return datetime.now().isoformat(sep=" ")

def load_avdat_version() -> str:
    """
    Load the AVDAT version.

    Returns:
        str: The AVDAT version.
    """
    version_file_name = os.path.join(GLOBAL_CONFIG['tmp_directory'], GLOBAL_CONFIG['avdat_version_file'])
    version = "0000"
    if DEBUG:    
        print("[%s] Looking for: %s" % (get_timestamp(), version_file_name))
    if not os.path.exists(version_file_name):
        raise Exception("[%s] Error: %s : %s" % (get_timestamp(), version_file_name, "File not found"))
    
    version = load_file(version_file_name)
    GLOBAL_CONFIG['last_avdat_version'] = version
    return version

def load_file(file_target: str, *, file_mode: str = "r") -> str:
    """
    Load content from a file.

    Args:
        file_target (str): The path of the file to load from.
        file_mode (str, optional): The mode to open the file in. Defaults to "r" (read mode).

    Returns:
        str: The content of the file.
    """
    if not os.path.exists(file_target):
        if DEBUG:
            print("[%s] File not found: %s" % (get_timestamp(), file_target))
        return None
    if DEBUG:
        print("[%s] Found file: %s" % (get_timestamp(), file_target))
    with open(file_target, file_mode) as open_file_target:  # read mode
        content = open_file_target.read()
        if DEBUG:
            print("[%s] loaded %s" % (get_timestamp(), file_target))
    return content

def update_avdat_version(version: str="0000") -> bool:
    """
    Write the AVDAT version to a file.

    Args:
        version (str): The AVDAT version.
    Returns:
        bool: True if the version is written to the file, False otherwise.
    """
    version_file_name = os.path.join(GLOBAL_CONFIG['tmp_directory'], GLOBAL_CONFIG['avdat_version_file'])
    if not os.path.exists(version_file_name):
        if not os.path.isdir(GLOBAL_CONFIG['tmp_directory']):
            os.makedirs(GLOBAL_CONFIG['tmp_directory'])
            if DEBUG:
                print("[%s] Created: %s" % (get_timestamp(), GLOBAL_CONFIG['tmp_directory']))
        if not version:
            version = "0000"
    GLOBAL_CONFIG['last_avdat_version'] = version
    return write_file(version_file_name, content_to_write=version, file_mode="w")

def write_file(file_target: str, *, file_mode: str = "a", content_to_write: str = "") -> bool:
    """
    Write content to a file.

    Args:
        file_target (str): The path of the file to write to.
        file_mode (str, optional): The mode to open the file in. Defaults to "a" (append mode).
        content_to_write (str, optional): The content to write to the file. Defaults to an empty string.
    """
    wrote_file = False
    if file_target:
        if DEBUG:
            print("[%s] Found file: %s" % (get_timestamp(), file_target))
        with open(file_target, file_mode) as open_file_target:  # append mode
            open_file_target.write(content_to_write)
            wrote_file = True
        if DEBUG:
            print("[%s] updated %s" % (get_timestamp(), file_target))
    else:
        if DEBUG:
            print("[%s] File not found: %s" % (get_timestamp(), file_target))
    return wrote_file

def initial_directory_setup(directory_path: str, initialize_directory: bool = True) -> bool:
    """
    Create a directory, delete if pre-existing.

    Args:
        directory_path (str): The path of the directory to create.

    Returns:
        bool: True if the directory is created, False otherwise.
    """
    bool_complete = False
    try:
        if os.path.exists(directory_path):
            if DEBUG:
                print("[%s] Found existing : %s" % (get_timestamp(), directory_path))
            if initialize_directory:
                if delete_directory(directory_path):
                    if DEBUG:
                        print("[%s] Deleted: %s" % (get_timestamp(), directory_path))
                    os.makedirs(directory_path)
                    if DEBUG:
                        print("[%s] Created: %s" % (get_timestamp(), directory_path))
        else:
            os.makedirs(directory_path)
            if DEBUG:
                print("[%s] Created: %s" % (get_timestamp(), directory_path))
        bool_complete = os.path.exists(directory_path)
    except OSError as e:
        raise OSError("[%s] Error: %s : %s" % (get_timestamp(), directory_path, e.strerror))
    return bool_complete

def is_system_directory(directory_path: str) -> bool:
    """
    Check if a directory is a system directory.

    Args:
        directory_path (str): The path of the directory to check.

    Returns:
        bool: True if the directory is a system directory, False otherwise.
    """
    return directory_path in GLOBAL_LIST_SYSTEM_DIRECTORIES

def delete_directory(directory_path: str) -> bool:
    """
    Delete a directory and its contents.

    Args:
        directory_path (str): The path of the directory to be deleted.

    Raises:
        OSError: If an error occurs while deleting the directory.

    """
    bool_complete = False
    # guard rails so we dont delete system directories
    if is_system_directory(directory_path):
        if DEBUG:
            raise OSError("[%s] Error: %s : %s" % (get_timestamp(), directory_path, "System directory"))
    else:
        if DEBUG:
            print("[%s] Not a system directory: %s" % (get_timestamp(), directory_path))
        try:
            shutil.rmtree(directory_path)
            if not os.path.exists(directory_path):
                bool_complete = True
        except OSError as e:
            raise OSError("[%s] Error: %s : %s" % (get_timestamp(), directory_path, e.strerror))
    return bool_complete

def download_tar_files(soup: BeautifulSoup, downloads_directory: str, url) -> list:
    """
    Find tar files in the HTML page.

    Args:
        soup (BeautifulSoup): The HTML page.

    Returns:
        list: A list of tar files.
    """
    files = []
    file_to_download = None
    current_version = None
    tarfile_download_path = None
    for link in soup.find_all('a'):
        proposed_version = None
        file  = link.get('href')
        if file.endswith(".tar"):
            # strip version off tarfile name
            if DEBUG:   
                print("[%s] Found tarfile: %s" % (get_timestamp(), file))
            url_tarfile_version = file.split('-')[1].split('.')[0]
            
            # if its our first file, set it as the file to download
            if current_version is None:
                current_version = url_tarfile_version 
            proposed_version = url_tarfile_version
            
            # if we have a file to download, check if its newer than the current version
            if url_tarfile_version <= GLOBAL_CONFIG['last_avdat_version']:
                if DEBUG:
                    print("[%s] AVDAT already downloaded" % get_timestamp())
                return files
            else:
                if DEBUG:
                    print("[%s] New AVDAT version found: %s" % (get_timestamp(), file.split('-')[1].split('.')[0]))
                if proposed_version > current_version:
                    file_to_download = file
                    tarfile_download_path = "%s/%s" % (downloads_directory, file_to_download)
                    current_version = proposed_version    
    # add the tarfile to the list of files
    files.append(tarfile_download_path)
    
    if tarfile_download_path is not None:
        if DEBUG:
            print("[%s] Downloading tarfile: %s" % (get_timestamp(), url + file_to_download))
        # download the tarfile
        urlretrieve(url + file_to_download, tarfile_download_path)
        if DEBUG:
            print("[%s] Downloaded tarfile: %s" % (get_timestamp(), tarfile_download_path))
    return files

def find_latest_tar_file(list_tarfiles: list) -> str:
    """
    Find the latest tar file from a list of tar files.

    Args:
        list_tarfiles (list): A list of tar files.

    Returns:
        str: The latest tar file.
    """
    latest_tarfile= None
    previous_tarfile= None
    for tarfile in list_tarfiles:
        if not latest_tarfile:
            latest_tarfile = tarfile
            if DEBUG:
                print("[%s] Adding Latest tarfile: %s" % (get_timestamp(), tarfile))
        else:
            current_version = latest_tarfile.split('-')[1]
            proposed_version = tarfile.split('-')[1]
            if proposed_version > current_version:
                previous_tarfile = latest_tarfile
                latest_tarfile = tarfile
                update_avdat_version(proposed_version)
                if DEBUG:
                    print("[%s] Added Newer tarfile: %s" % (get_timestamp(), latest_tarfile))
            try:
                if DEBUG:
                    print("[%s] Removing older tarfile: %s" % (get_timestamp(), previous_tarfile))
                if previous_tarfile:
                    os.remove(previous_tarfile)
            except Exception as e:
                pass                
    if DEBUG:
        print("[%s] Latest file: %s" % (get_timestamp(), latest_tarfile))
    return latest_tarfile

def get_tarfile_basename(tarfile: str) -> str:
    """
    Get the basename of a tar file.

    Args:
        tarfile (str): The path of the tar file.

    Returns:
        str: The basename of the tar file.
    """
    return os.path.basename(tarfile)

def get_soup(url: str) -> BeautifulSoup:
    """
    Get the HTML page from a URL.

    Args:
        url (str): The URL of the HTML page.

    Returns:
        BeautifulSoup: The HTML page.
    """
    r  = requests.get(url)
    data = r.text
    return BeautifulSoup(data, features="lxml")

def load_config() -> dict:
    """
    Load the configuration.

    Returns:
        dict: The configuration.
    """
    
    parse_config()
    
    return GLOBAL_CONFIG

def parse_config():
    """
    Parses the global configuration and performs directory setup based on the configuration values.

    Raises:
        OSError: If directory creation fails.
    """
    for k,v in GLOBAL_CONFIG.items():
        if k == 'cache_directory' or k == 'tmp_directory':
            if k == 'tmp_directory':
                # see if theres a tmp directory
                # if not create it
                if not os.path.exists(v):
                    if update_avdat_version():
                        print("[%s] Created: %s" % (get_timestamp(), v))
                if not initial_directory_setup(v, initialize_directory=False):
                    raise OSError("[%s] Error: %s : %s" % (get_timestamp(), v, "Something went wrong with tmp directory creation")) 
                
            else:
                if not initial_directory_setup(v):
                    raise OSError("[%s] Error: %s : %s" % (get_timestamp(), v, "Directory creation failed"))
                
def run_subprocess(cmd: str) -> list:
    """
    Executes a command and returns the output as a list of lines.

    Returns:
        list: The output of the command as a list of lines.
    """
    lines = []
    try:
        output = subprocess.check_output(cmd, shell=True)
        lines = output.decode().splitlines()
    except subprocess.CalledProcessError as e:
        if DEBUG:
            print("[%s] Error: %s : %s" % (get_timestamp(), cmd, e))
    return lines

def run_additional_cmds(cmds: dict = {}):
    """
    Run additional commands.
    """
    for cmd_name, cmd in cmds.items():
        if DEBUG:
            print("[%s] Running: \n\t[ %s ]:\t%s" % (get_timestamp(), cmd_name, cmd))
        call_back_data = run_subprocess(cmd)
        if DEBUG:
            print("\n\t\t[%s] Callback:\t\n" % (get_timestamp()))
            for entry in call_back_data:
                print("\n\t\tCallback data:\t%s\n" % (entry))

def main():
    """
    entry point of the program.
    It performs the necessary steps to download and process tar files in preparation of deployment.
    """
    load_config()
    
    latest_tarfile= None
    
    # load the last avdat version
    last_version_downloaded = load_avdat_version()
    
    #get soup object for the url
    soup = get_soup(GLOBAL_CONFIG['tar_files_url'])
    
    if DEBUG:
        print("[%s] Using : %s" % (get_timestamp(), GLOBAL_CONFIG['tar_files_url']))
    
    if DEBUG:
        print("[%s] Last avdat version downloaded: %s" % (get_timestamp(), GLOBAL_CONFIG['last_avdat_version']))
        
    # initialize directories:
    #   delete the directory if it exists
    #   create the directory
    # find tar files
    list_tarfiles= download_tar_files(soup, GLOBAL_CONFIG['cache_directory'], GLOBAL_CONFIG['tar_files_url']) 
    
    # if there are no tar files, exit
    if not list_tarfiles:
        if DEBUG:
            print("[%s] No new avdat version found" % get_timestamp())
        return
    
    # find the latest tar file
    latest_tarfile= find_latest_tar_file(list_tarfiles)
    last_version_downloaded = latest_tarfile.split('-')[1].split('.')[0]
    
    if DEBUG:
        print("[%s] last avdat version: %s" % (get_timestamp(), last_version_downloaded))  
    try:
        # find the latest tar file basename
        # build the final avdat tar file path
        # initialize the save directory
        # move the latest tar file to the save directory
        # store the avdat version
        tarfile_basename = get_tarfile_basename(latest_tarfile)
        final_avdat_tarfile = os.path.join(GLOBAL_CONFIG['save_directory'], tarfile_basename)
        initial_directory_setup(GLOBAL_CONFIG['save_directory'])
        shutil.move(latest_tarfile, final_avdat_tarfile)
        update_avdat_version(final_avdat_tarfile.split('-')[1].split('.')[0])
        if DEBUG:
            print("[%s] Latest AVDAT tarfile saved: %s" % (get_timestamp(), final_avdat_tarfile))
            print("\n[%s] Prepping file for deployment: \n" % get_timestamp())
        
        run_additional_cmds(GLOBAL_ADDITIONAL_CMDS)
        
        if DEBUG:
            print("[%s] Completed." % get_timestamp())
    except Exception as e:
        if DEBUG:
            print("[%s] Error: %s : %s" % (get_timestamp(), final_avdat_tarfile, e))
        raise Exception("[%s] Error: %s : %s" % (get_timestamp(), final_avdat_tarfile, e))

# Check if the script is run as the main module
if __name__ == "__main__":
    # Call the main function
    if DEBUG:    
        print("[%s] Starting..." % get_timestamp())
    try:
        main()
    except Exception as e:
        print(str(e))