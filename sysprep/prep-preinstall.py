import os

GLOBAL_PREINSTALL_CONFIG = {
    'service_enable': 'systemctl disable fapolicyd',
    'service_start': 'systemctl stop fapolicyd',
    'service_start': 'systemctl disable firewalld',
    'service_start': 'systemctl stop firewalld',
} 

def execute_commands(config: dict):
    for systemd_command in config.values():
        os.system(systemd_command)
        print(f"Command '{systemd_command}' has been executed")

def main():
    execute_commands(GLOBAL_PREINSTALL_CONFIG)

if __name__ == "__main__": 
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")