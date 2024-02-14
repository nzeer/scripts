# Import the datetime and time modules
import datetime
import time

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
    if difference >= 72 * 60 * 60:
        # Return True
        print("long running")
        return True
    else:
        # Return False
        print("its fine")
        return False
    
def main():
    # ps -eo user,pid,lstart,cmd
    is_running_long("Tue Jan 14 11:47:15 2024")
    
    # Check if the script is run as the main module
if __name__ == "__main__":
    # Call the main function
    main()