# Import the os and subprocess modules
import os
import subprocess


# Define a function to run an Ansible playbook
def run_playbook(playbook, extra_vars):
    # Build the command to run the playbook with the extra variables
    command = ["ansible-playbook", playbook, "-e", extra_vars]
    # Run the command and capture the output
    output = subprocess.run(command, capture_output=True, text=True)
    # Check if the command was successful
    if output.returncode == 0:
        # Print the output
        print(output.stdout)
    else:
        # Print the error
        print(output.stderr)


# Define a function to gather facts from a network CIDR
def gather_facts(network_cidr):
    # Define the playbook name
    print(network_cidr)
    playbook = "gather_facts.yml"
    # Define the extra variables as a JSON string
    extra_vars = f'{{"network_cidr": "{network_cidr}"}}'
    # Call the run_playbook function
    run_playbook(playbook, extra_vars)


# Define a main function
def main():
    # Get the network CIDR from the user input
    network_cidr = "172.16.0.24/0"  # input("Enter the network CIDR: ")
    # network_cidr = input("Enter the network CIDR: ")
    # Call the gather_facts function
    gather_facts(network_cidr)


# Check if the script is run as the main module
if __name__ == "__main__":
    try:
        # Call the main function
        main()
    except Exception as e:
        print("Oops: ", e)
