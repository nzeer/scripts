import os
import configparser

# Initialize the configparser
config = configparser.ConfigParser()

# Read the configuration file
config.read('config.ini')

GLOBAL_CONFIG_HOSTNAME = {
    'hostname': config.get('hostname', 'hostname'),
    'human_readable_hostname': config.get('hostname', 'human_readable_hostname')
}

def set_hostname(hostname: str = GLOBAL_CONFIG_HOSTNAME['hostname']):
    os.system(f"hostnamectl set-hostname {hostname}")
    
def set_human_readable_hostname(human_readable_hostname: str = GLOBAL_CONFIG_HOSTNAME['human_readable_hostname']):
    os.system(f"echo {human_readable_hostname} > /etc/humanhostname")
    

    
if __name__ == "__main__":
    try:
        set_hostname()
        set_human_readable_hostname()
        #os.system("shutdown -r now")
    except Exception as e:
        print(f"An error occurred: {e}")