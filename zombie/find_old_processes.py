import os
import subprocess
import datetime
import time

CMD = "ps -eo user,pid,lstart,cmd |grep -i id=tcserver"
RUNTIME = 72 * 60 * 60


# Define a function to parse the date string into a datetime object
def parse_date(date_string):
    # Use the datetime.strptime() function with the appropriate format string
    # ps -eo user,pid,lstart,cmd
    date_object = datetime.datetime.strptime(date_string, "%a %b %d %H:%M:%S %Y")
    # Return the datetime object
    return date_object


# Define a function to convert the datetime object to a POSIX timestamp
def get_timestamp(date_object):
    # Use the time.mktime() function to convert the datetime object to a POSIX timestamp
    timestamp = time.mktime(date_object.timetuple())
    # Return the timestamp
    return timestamp


# Define a function to determine if a linux process has been running for 72 hours
def is_running_long(date_string):
    # Call the parse_date() function and get the datetime object
    date_object = parse_date(date_string)
    # Call the get_timestamp() function and get the POSIX timestamp
    timestamp = get_timestamp(date_object)
    # Get the current POSIX timestamp
    current = time.time()
    # Calculate the difference between the current and the process timestamps
    difference = current - timestamp
    # Check if the difference is greater than or equal to 72 hours in seconds
    if difference >= RUNTIME:
        # Return True
        return difference
    else:
        # Return False
        return 0


# Define a function to run the ps command and get the output
def run_ps():
    output = subprocess.check_output(CMD, shell=True)
    lines = output.decode().splitlines()
    return lines


# Define a function to filter the lines by the elapsed time
def filter_lines(lines):
    # Initialize an empty list to store the filtered lines
    filtered = []
    # Loop through the lines
    for line in lines:
        # Split the line by whitespace
        columns = line.split()
        # compose time signature
        etime = "%s %s %s %s %s" % (
            columns[2],
            columns[3],
            columns[4],
            columns[5],
            columns[6],
        )
        diff = is_running_long(etime)
        if diff > 0:
            # store the pid
            pid = columns[1]
            # calculate the difference in minutes
            diff_mins = int(diff / 60 / 60)
            # format the output for nagios
            # Append the line to the filtered list
            filtered.append("%s-%s" % (pid, diff_mins))
    # Return the filtered list
    return filtered


# Define a main function
def main():
    # Call the run_ps function and get the lines
    lines = run_ps()
    # Call the filter_lines function and get the filtered lines
    filtered = filter_lines(lines)
    # Print the filtered lines
    for line in filtered:
        print(line)


# Check if the script is run as the main module
if __name__ == "__main__":
    # Call the main function
    main()
