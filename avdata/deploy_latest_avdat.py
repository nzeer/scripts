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

import configparser
import logging
import colorlog
from urllib.request import urlretrieve
from bs4 import BeautifulSoup
import requests
import os
import shutil
import subprocess

GLOBAL_CONFIG_PATH = "./config.ini"

# Load configuration
config = configparser.ConfigParser()
config.read(GLOBAL_CONFIG_PATH)

# Variables defined from the config file
save_directory = config['FILESYSTEM']['save_directory']
cache_directory = config['FILESYSTEM']['cache_directory']
tmp_directory = config['FILESYSTEM']['tmp_directory']

avdat_version_file = config['AVDAT']['avdat_version_file']
last_avdat_version = config['AVDAT']['last_avdat_version']
tar_files_url = config['AVDAT']['tar_files_url']

log_file = config['LOGGING']['log_file']

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Set the log level to INFO

# Create console handler and set level to debug
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create a formatter with color
formatter = colorlog.ColoredFormatter(
    "%(blue)s[%(asctime)s] %(log_color)s%(levelname)-8s%(reset)s %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)

# Create file handler and set level to debug
file_handler = logging.FileHandler(log_file)  # Log messages to this file
file_handler.setLevel(logging.DEBUG)

# Create formatter and add it to the handlers
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Now you can use logging as before
logging.info("Initializing logging...")


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

def load_avdat_version() -> str:
    """
    Load the AVDAT version from the specified file.

    Returns:
        str: The AVDAT version.
    
    Raises:
        Exception: If the version file is not found.
    """
    version_file_name = os.path.join(tmp_directory, avdat_version_file)
    version = "0000"
    logging.info(f"Loading: {version_file_name}")  
    if not os.path.exists(version_file_name):
        logging.error(f"Error: {version_file_name} : File not found")
        raise Exception(f"Error: {version_file_name} : File not found")
    
    version = load_file(version_file_name)
    global last_avdat_version
    last_avdat_version = version
    return version

def load_file(file_target: str, *, file_mode: str = "r") -> str:
    """
    Load the content of a file.

    Args:
        file_target (str): The path to the file.
        file_mode (str, optional): The file mode to open the file in. Defaults to "r".

    Returns:
        str: The content of the file.

    Raises:
        None

    """
    if not os.path.exists(file_target):
        logging.warn(f"File not found: {file_target}")
        return None
    logging.info(f"Found file: {file_target}")
    with open(file_target, file_mode) as open_file_target:
        content = open_file_target.read()
        logging.info(f"loaded {file_target}")
    return content

def update_avdat_version(version: str="0000") -> bool:
    """
    Update the AVDAT version.

    Args:
        version (str): The AVDAT version to update. Defaults to "0000".

    Returns:
        bool: True if the version is successfully updated, False otherwise.
    """
    version_file_name = os.path.join(tmp_directory, avdat_version_file)
    if not os.path.exists(version_file_name):
        if not os.path.isdir(tmp_directory):
            os.makedirs(tmp_directory)
            logging.info(f"Created: {tmp_directory}")
        if not version:
            version = "0000"
    global last_avdat_version
    last_avdat_version = version
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
        logging.info(f"Found file: {file_target}")
        with open(file_target, file_mode) as open_file_target:  # append mode
            open_file_target.write(content_to_write)
            wrote_file = True
        logging.info(f"updated {file_target}")
    else:
        logging.warn(f"File not found: {file_target}")
    return wrote_file

def initial_directory_setup(directory_path: str, initialize_directory: bool = True) -> bool:
    """
    Initializes the directory at the given path.

    Args:
        directory_path (str): The path of the directory to be initialized.
        initialize_directory (bool, optional): Flag to indicate whether to initialize the directory. 
            If set to False, the existing directory will not be deleted. Defaults to True.

    Returns:
        bool: True if the directory is successfully initialized, False otherwise.
    """
    bool_complete = False
    try:
        if os.path.exists(directory_path):
            logging.info(f"Found existing : {directory_path}")
            if initialize_directory:
                if delete_directory(directory_path):
                    logging.info(f"Deleted: {directory_path}")
                    os.makedirs(directory_path)
                    logging.info(f"Created: {directory_path}")
        else:
            os.makedirs(directory_path)
            logging.info(f"Created: {directory_path}")
        bool_complete = os.path.exists(directory_path)
    except OSError as e:
        logging.error(f"Error: {directory_path} : {e.strerror}")
        raise OSError(f"Error: {directory_path} : {e.strerror}")
    return bool_complete

def is_system_directory(directory_path: str) -> bool:
    """
    Check if a directory is a system directory.

    Args:
        directory_path (str): The path of the directory to check.

    Returns:
        bool: True if the directory is a system directory, False otherwise.
    """
    logging.debug(f"Checking: {directory_path}")
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
        logging.Error(f"Found system directory: {directory_path}")
        raise OSError(f"Found system directory: {directory_path}")
    else:
        logging.debug(f"Not a system directory: {directory_path}")
        logging.info(f"Deleting: {directory_path}")
        try:
            shutil.rmtree(directory_path)
            if not os.path.exists(directory_path):
                bool_complete = True
        except OSError as e:
            logging.error(f"Error: {directory_path} : {e.strerror}")
            raise OSError(f"Error: {directory_path} : {e.strerror}")
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
            logging.info(f"Found tarfile: {file}")   
            url_tarfile_version = file.split('-')[1].split('.')[0]
            # if its our first file, set it as the file to download
            if current_version is None:
                current_version = url_tarfile_version 
            proposed_version = url_tarfile_version
            
            # if we have a file to download, check if its newer than the current version
            if url_tarfile_version == last_avdat_version:
                logging.info(f"AVDAT: {url_tarfile_version} already downloaded")
                return files
            elif url_tarfile_version > last_avdat_version:
                logging.info(f"New AVDAT version found: {file.split('-')[1].split('.')[0]}")
                if proposed_version > current_version:
                    file_to_download = file
                    tarfile_download_path = "%s/%s" % (downloads_directory, file_to_download)
                    logging.debug(f"Added file to download: {url + file_to_download}")
                    current_version = proposed_version
            else:
                logging.info(f"Older AVDAT version found: {file.split('-')[1].split('.')[0]}")    
    # add the tarfile to the list of files
    files.append(tarfile_download_path)
    
    # download the tarfile
    # try 3 times
    if tarfile_download_path is not None:
        for i in range(3):
            try:
                logging.info(f"Downloading tarfile: {url + file_to_download}")
                # download the tarfile
                urlretrieve(url + file_to_download, tarfile_download_path)
                if os.path.exists(tarfile_download_path):
                    logging.debug(f"Downloaded tarfile: {tarfile_download_path}")
                    break
            except Exception as e:
                logging.error(f"Error: {url + file_to_download} : {e}")
                if i<3:
                    continue
                raise Exception(f"Error: {url + file_to_download} : {e}")
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
            logging.info(f"Adding Latest tarfile: {tarfile}")
        else:
            current_version = latest_tarfile.split('-')[1]
            proposed_version = tarfile.split('-')[1]
            if proposed_version > current_version:
                previous_tarfile = latest_tarfile
                latest_tarfile = tarfile
                update_avdat_version(proposed_version)
                logging.info(f"Added Newer tarfile: {latest_tarfile}")
            try:
                logging.debug(f"Removing older tarfile: {previous_tarfile}")
                if previous_tarfile:
                    os.remove(previous_tarfile)
            except Exception as e:
                logging.warn(f"Warn: {previous_tarfile} : {e}")
                pass                
    logging.info(f"Latest file: {latest_tarfile}")
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

def load_config():
    """
    Load the configuration.

    Returns:
        dict: The configuration.
    """
    parse_config()
    
def parse_config():
    """
    Parses the global configuration and performs directory setup based on the configuration values.

    Raises:
        OSError: If directory creation fails.
    """
    if tmp_directory:
        # see if theres a tmp directory
        # if not create it
        if not os.path.exists(tmp_directory):
            if update_avdat_version():
                logging.info(f"Created tmp directory: {tmp_directory}")
        if not initial_directory_setup(tmp_directory, initialize_directory=False):
            logging.error(f"Something went wrong with tmp directory creation: {tmp_directory}")
            raise OSError(f"Something went wrong with tmp directory creation: {tmp_directory}") 
    
    # see if theres a cache directory
    # if not create it    
    if cache_directory:
        if not initial_directory_setup(cache_directory):
            logging.error(f"Directory creation failed: {cache_directory}")
            raise OSError(f"Directory creation failed: {cache_directory}")
                
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
        logging.error(f"{cmd} : {e}")
    return lines

def run_additional_cmds(cmds: dict = {}):
    """
    Run additional commands.
    """
    for cmd_name, cmd in cmds.items():
        logging.info(f"Running: \n\t[ {cmd_name} ]:\t{cmd}")
        call_back_data = run_subprocess(cmd)
        logging.info(f"Callback:\t\n")
        for entry in call_back_data:
            logging.info(f"Callback data:\t{entry}")

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
    soup = get_soup(tar_files_url)
    
    logging.info(f"Using : {tar_files_url}")
    
    logging.info(f"Last avdat version downloaded: {last_avdat_version}")
        
    # initialize directories:
    #   delete the directory if it exists
    #   create the directory
    # find tar files
    list_tarfiles= download_tar_files(soup, cache_directory, tar_files_url) 
    
    # if there are no tar files, exit
    if not list_tarfiles:
        logging.info(f"No new avdat version found")
        logging.info(f"Completed.")
        return
    
    # find the latest tar file
    latest_tarfile= find_latest_tar_file(list_tarfiles)
    last_version_downloaded = latest_tarfile.split('-')[1].split('.')[0]
    
    logging.info(f"Latest AVDAT tarfile: {latest_tarfile}")
    try:
        # find the latest tar file basename
        # build the final avdat tar file path
        # initialize the save directory
        # move the latest tar file to the save directory
        # store the avdat version
        tarfile_basename = get_tarfile_basename(latest_tarfile)
        final_avdat_tarfile = os.path.join(save_directory, tarfile_basename)
        initial_directory_setup(save_directory)
        shutil.move(latest_tarfile, final_avdat_tarfile)
        update_avdat_version(final_avdat_tarfile.split('-')[1].split('.')[0])
        
        logging.info(f"Latest AVDAT tarfile saved: {final_avdat_tarfile}")
        logging.info(f"Prepping file for deployment...")
        
        run_additional_cmds(GLOBAL_ADDITIONAL_CMDS)
        
        logging.info(f"Completed.")
    except Exception as e:
        logging.error(f": {final_avdat_tarfile} : {e}")
        raise Exception(f": {final_avdat_tarfile} : {e}")

# Check if the script is run as the main module
if __name__ == "__main__":
    # Call the main function
    logging.info(f"Starting...")    
    
    try:
        main()
    except Exception as e:
        logging.error(f": {e}")