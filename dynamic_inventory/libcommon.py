import os
import pathlib as p
import shutil
from datetime import datetime
import errno
import glob

DEBUG = True

def sanitize_directory(top_level_path):
    """
    Delete contents of a given top level directory.
    Args:
        top_level_path (str): The path of the top level directory
    """
    try:
        for root, dirs, files in os.walk(top_level_path):
            for file in files:
                file_path = os.path.join(root, file)
                os.remove(file_path)
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                shutil.rmtree(dir_path)
    except OSError:
        pass
def write_file(file_target, file_mode="a", content_to_write=""):
    """
    Write content to a file.
    Args:
        file_target (str): The path of the file to write to.
        file_mode (str, optional): The mode to open the file in. Defaults to "a" (append mode).
        content_to_write (str, optional): The content to write to the file. Defaults to an empty string.
    """
    if DEBUG:
        print("[%s] Found file: %s" % (get_timestamp(), file_target))
    with open(file_target, file_mode) as open_file_target:  # append mode
        open_file_target.write(content_to_write)
        if DEBUG:
            print("[%s] updated %s" % (get_timestamp(), file_target))

def glob_files(location="./", file_extension="*.list", is_recursive=True) -> set:
    """
    Search for files with a specific file extension in a given location.
    Args:
        location (str, optional): The location to search for files. Defaults to "./".
        file_extension (str, optional): The file extension to match. Defaults to "*.list".
        is_recursive (bool, optional): Whether to search recursively in subdirectories. Defaults to True.
    Returns:
        set: A set of file paths matching the given criteria.
    """
    glob_listfiles_path = "%s/**/%s" % (location, file_extension)
    return set(glob.glob(glob_listfiles_path, recursive=is_recursive))

def get_timestamp() -> str:
    """
    Returns the current timestamp in ISO 8601 format.
    :return: The current timestamp as a string.
    """
    return datetime.now().isoformat(sep=" ")

def delete_directory(directory_path):
    """
    Delete a directory and its contents.
    Args:
        directory_path (str): The path of the directory to be deleted.
    Raises:
        OSError: If an error occurs while deleting the directory.
    """
    try:
        shutil.rmtree(directory_path)
        if DEBUG:
            print("[%s] Deleted directory: %s" % (get_timestamp(), directory_path))
    except OSError as e:
        print("[%s] Error: %s : %s" % (get_timestamp(), directory_path, e.strerror))

def initialize_directory(directory_path) -> bool:
    """
    Initializes a directory by creating it if it doesn't exist, or deleting and recreating it if it does exist.
    Args:
        directory_path (str): The path of the directory to initialize.
    Returns:
        bool: True if the directory was successfully initialized, False otherwise.
    """
    path_directory_path = p.Path(directory_path)
    if path_directory_path.exists():
        if DEBUG:
            print("[%s] Found directory: %s" % (get_timestamp(), directory_path))
        delete_directory(directory_path)
    path_directory_path.mkdir()
    if DEBUG:
        print("[%s] Initialized directory: %s" % (get_timestamp(), directory_path))
    return True

""" =========================================================
Create destination directory and clone everything from source 
directory into destination directory. 
============================================================="""

def clone_everything(src, dst) -> bool:
    """
    Copy files and directories from source to destination.
    Args:
        src (str): The path of the source directory or file.
        dst (str): The path of the destination directory or file.
    Returns:
        bool: True if the copying is successful, False otherwise.
    """
    try:
        shutil.copytree(src, dst)
        if DEBUG:
            print("[%s] copying %s to %s" % (get_timestamp(), src, dst))
    except OSError as exc:  # python >2.5
        if exc.errno in (errno.ENOTDIR, errno.EINVAL):
            shutil.copy(src, dst)
            if DEBUG:
                print("[%s] copying %s to %s" % (get_timestamp(), src, dst))
        else:
            raise
    return True

def merge_files(file_src, file_dst):
    """
    Merge the contents of the source file into the destination file.
    Args:
        file_src (str): The path to the source file.
        file_dst (str): The path to the destination file.
    Returns:
        None
    """
    if os.path.exists(file_src) and os.path.exists(file_dst):
        with open(file_src, 'r') as src, open(file_dst, 'a') as dst:
            shutil.copyfileobj(src, dst)
