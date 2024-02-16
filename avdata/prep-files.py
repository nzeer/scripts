from urllib.request import urlretrieve
from bs4 import BeautifulSoup
import requests
import os
import shutil

DEBUG = True

url = "https://update.nai.com/products/datfiles/4.x/"
save_directory = "./dat_file"
cache_directory = "./.cache"

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

def main():
    r  = requests.get(url)
    data = r.text
    soup = BeautifulSoup(data, features="lxml")
    files = []

    if os.path.exists(save_directory):
        delete_directory(save_directory)
    else:
        os.makedirs(save_directory)
        
    if os.path.exists(cache_directory):
        delete_directory(cache_directory)
    else:
        os.makedirs(cache_directory)

    for link in soup.find_all('a'):
        file  = link.get('href')
        if DEBUG:
            print(file)
        if file.endswith(".tar"):
            files.append("%s/%s" % (cache_directory, file))
            if DEBUG:
                print("found tar: ", file)
            urlretrieve(url + file, cache_directory + "/" + file)
            
    latest = "" 
    for item in files:
        if not latest:
            if DEBUG:
                print("First: ", item)
            latest = item
        else:
            if item.split('-')[1] > latest.split('-')[1]:
                if DEBUG:
                    print("Newer: ", item)
                    print("Older: ", latest)
                latest = item
            else:
                if DEBUG:
                    print("Removing: ", item)
                os.remove(item)
                
    if DEBUG:
        print("Latest file: ", latest)

    shutil.move(latest, "%s/%s" % (save_directory, os.path.basename(latest)))


# Check if the script is run as the main module
if __name__ == "__main__":
    # Call the main function
    main()