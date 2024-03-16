import os

GLOBAL_YUM_ACTION_CONFIG = {
    'yum_clean_update': 'yum clean all && yum update -y',
} 

def execute_commands(config: dict):
    for command in config.values():
        os.system(command)
        print(f"Command '{command}' has been executed")

def main():
    execute_commands(GLOBAL_YUM_ACTION_CONFIG)

if __name__ == "__main__": 
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")