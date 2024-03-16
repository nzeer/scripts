import os

GLOBAL_NAGIOS_SERVICE_CONFIG = {
    'service_enable': 'systemctl enable ncpa.service',
    'service_start': 'systemctl start ncpa.service'
} 

def execute_commands(config: dict):
    for command in config.values():
        os.system(command)

def main():
    execute_commands(GLOBAL_NAGIOS_SERVICE_CONFIG)

if __name__ == "__main__": 
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")