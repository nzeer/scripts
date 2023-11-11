# Import the os and subprocess modules
import os
import subprocess
import sys


# Define a function to run git pull in a given directory
def git_pull(directory):
    # Change the current working directory to the given directory
    os.chdir(directory)
    # Run the git pull command and capture the output
    output = subprocess.run(["git", "pull"], capture_output=True, text=True)
    # Check if the command was successful
    if output.returncode == 0:
        # Print the output
        print(output.stdout)
    else:
        # Print the error
        print(output.stderr)


# Define a function to loop through all top level directories in a given path
def loop_directories(path):
    try:  # Loop through the files and directories in the path
        if not os.path.exists(path):
            raise Exception("Path does not exist")
        for entry in os.scandir(path):
            # Check if the entry is a directory
            if entry.is_dir():
                # Try to run git pull in the directory
                try:
                    git_pull(entry.path)
                    # Handle any exceptions
                except Exception as e:
                    # Print the exception
                    print("Oops: ", e)
            pass
        # continue

    except Exception as e:
        # Print the exception
        print("Oops: ", e)
        pass


# Define a main function
def main():
    # Get the path from the user input or use the current working directory as the default
    # path = input("Enter the path: ") or os.getcwd()
    # Check if the user provided a directory as an argument
    if len(sys.argv) > 1:
        # Get the directory from the first argument
        path = sys.argv[1]
    else:
        # Use the current working directory as the default
        path = os.getcwd()
    # Print the path
    print(f"Looping through all top level directories in {path}")
    # Call the loop_directories function
    loop_directories(path)


# Check if the script is run as the main module
if __name__ == "__main__":
    # Call the main function
    main()
