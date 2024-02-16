from doctest import debug
import os
import pathlib as p
import shutil
from datetime import datetime
import errno
import time
import glob
import subprocess

DEBUG = False

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

def write_file(file_target: str, *, file_mode: str = "a", content_to_write: str = ""):
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

def glob_files(location: str = "./", file_extension: str = "*.list", is_recursive: bool = True) -> set:
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
            print("[%s] Error: %s : %s" % (get_timestamp(), directory_path, "System directory"))
            raise OSError("Error: %s : %s" % (directory_path, "System directory"))
        else:
            try:
                shutil.rmtree(directory_path)
                if not os.path.exists(directory_path):
                    bool_complete = True
                    if DEBUG:
                        print("[%s] Deleted directory: %s" % (get_timestamp(), directory_path))
            except OSError as e:
                if DEBUG:
                    print("[%s] Error: %s : %s" % (get_timestamp(), directory_path, e.strerror))
                raise OSError("Error: %s : %s" % (directory_path, e.strerror))
    return bool_complete

def initialize_directory(directory_path: str) -> bool:
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
    return path_directory_path.exists()

def clone_everything(src: str, dst: str) -> bool:
    """
    Copy files and directories from source to destination.

    Args:
        src (str): The path of the source directory or file.
        dst (str): The path of the destination directory or file.

    Returns:
        bool: True if the copying is successful, False otherwise.
    """
    bool_complete = False
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
            raise exc
    finally:
        bool_complete = True
    return bool_complete

def merge_files(file_src: str, file_dst: str) -> bool:
    """
    Merge the contents of the source file into the destination file.

    Args:
        file_src (str): The path to the source file.
        file_dst (str): The path to the destination file.

    Returns:
        None
    """
    bool_complete = False
    if os.path.exists(file_src) and os.path.exists(file_dst):
        with open(file_src, 'r') as src, open(file_dst, 'a') as dst:
            shutil.copyfileobj(src, dst)
        bool_complete = True
    return bool_complete

def parse_date(date_string: str) -> datetime:
    """
    Parse a date string into a datetime object.

    Args:
        date_string (str): The date string to be parsed.

    Returns:
        datetime.datetime: The parsed datetime object.
    """
    date_object = datetime.datetime.strptime(date_string, "%a %b %d %H:%M:%S %Y")
    return date_object

def get_timestamp(date_object: datetime) -> float:
    """
    Converts a datetime object to a POSIX timestamp.

    Args:
        date_object (datetime): The datetime object to convert.

    Returns:
        float: The POSIX timestamp representing the given datetime object.
    """
    timestamp = time.mktime(date_object.timetuple())
    return timestamp

def run_ps(cmd: str = "ps -ef") -> list:
    """
    Executes a command and returns the output as a list of lines.

    Returns:
        list: The output of the command as a list of lines.
    """
    #cmd = "ps -eo user,pid,lstart,cmd |grep -i id=tcserver"
    output = subprocess.check_output(cmd, shell=True)
    lines = output.decode().splitlines()
    return lines

