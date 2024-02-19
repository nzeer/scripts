import tarfile
from urllib.request import urlretrieve
from bs4 import BeautifulSoup
from flask import config
import requests
import os
import shutil

DEBUG = True

CONFIG = {
    'save_directory': "./dat_file",
    'cache_directory': "./.cache",
    'tar_files_url': "https://update.nai.com/products/datfiles/4.x/",
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

def initial_directory_setup(directory_path: str) -> bool:
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
            delete_directory(directory_path)
        
        os.makedirs(directory_path)
        if os.path.exists(directory_path):
            bool_complete = True
    except OSError as e:
        raise OSError("Error: %s : %s" % (directory_path, e.strerror))
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
            raise OSError("Error: %s : %s" % (directory_path, "System directory"))
        else:
            try:
                shutil.rmtree(directory_path)
                if not os.path.exists(directory_path):
                    bool_complete = True
            except OSError as e:
                raise OSError("Error: %s : %s" % (directory_path, e.strerror))
    return bool_complete

def find_tar_files(soup: BeautifulSoup, downloads_directory: str, url) -> list:
    """
    Find tar files in the HTML page.

    Args:
        soup (BeautifulSoup): The HTML page.

    Returns:
        list: A list of tar files.
    """
    files = []
    for link in soup.find_all('a'):
        file  = link.get('href')
        if DEBUG:
            print(file)
        if file.endswith(".tar"):
            files.append("%s/%s" % (downloads_directory, file))
            if DEBUG:
                print("found tar: ", file)
            urlretrieve(url + file, downloads_directory + "/" + file)
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
    for tarfile in list_tarfiles:
        if not latest_tarfile:
            if DEBUG:
                print("First: ", tarfile)
            latest_tarfile = tarfile
        else:
            if tarfile.split('-')[1] > latest_tarfile.split('-')[1]:
                if DEBUG:
                    print("Newer: ", tarfile)
                    print("Older: ", latest_tarfile)
                latest_tarfile = tarfile
            else:
                if DEBUG:
                    print("Removing: ", tarfile)
                os.remove(tarfile)
                
    if DEBUG:
        print("Latest file: ", latest_tarfile)
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

def main():
    """
    entry point of the program.
    It performs the necessary steps to download and process tar files in preparation of deployment.
    """
    latest_tarfile= None
    
    #get soup object for the url
    soup = get_soup(CONFIG['tar_files_url'])
    
    # initialize directories
    # delete the directory if it exists
    # create the directory
    for k,v in CONFIG.items():
        if not initial_directory_setup(v):
            raise OSError("Error: %s : %s" % (v, "Directory creation failed"))
        
    # find tar files
    list_tarfiles= find_tar_files(soup, CONFIG['cache_directory'], CONFIG['tar_files_url']) 
    
    # find the latest tar file
    latest_tarfile= find_latest_tar_file(list_tarfiles)
    
    if DEBUG:
        print("Latest file: ", latest_tarfile)
    
    try:
        # move the latest tar file to the save directory
        tarfile_basename = get_tarfile_basename(latest_tarfile)
        shutil.move(latest_tarfile, "%s/%s" % (CONFIG['save_directory'], tarfile_basename))
        if DEBUG:
            print("Moved: ", latest_tarfile)
    except Exception as e:
        if DEBUG:
            print("Error: %s : %s" % (latest_tarfile, e.strerror))
        raise Exception("Error: %s : %s" % (latest_tarfile, e.strerror))

# Check if the script is run as the main module
if __name__ == "__main__":
    # Call the main function
    try:
        main()
    except Exception as e:
        print(str(e))