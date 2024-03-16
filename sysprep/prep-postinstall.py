import os

GLOBAL_POST_INSTALL_CONFIG = {
    'avdat_check': '/usr/local/scripts/avdat-check.sh',
    'passwdcheck': '/usr/local/scripts/passwdcheck.sh'
} 

def script_exists(directory: str) -> bool:
    return os.path.exists(directory)

def execute_scripts(config: dict):
    for script in config.values():
        if script_exists(script):
            os.system(script)

def main():
    execute_scripts(GLOBAL_POST_INSTALL_CONFIG)

if __name__ == "__main__": 
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
