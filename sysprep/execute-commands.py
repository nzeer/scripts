import os

GLOBAL_COMMAND_CONFIG = {
    'service_enable': 'systemctl enable something',
    'service_start': 'systemctl start something',
    'yum_clean': 'yum clean all',
    'yum_update': 'yum update -y',
} 

def execute_commands(config: dict):
    for command in config.values():
        os.system(command)
        print(f"Command '{command}' has been executed")

def main():
    execute_commands(GLOBAL_COMMAND_CONFIG)

if __name__ == "__main__": 
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")