import shutil
import os
import configparser
from turtle import back
from jinja2 import Template
import jinja2

# Initialize the configparser
config = configparser.ConfigParser()

# Read the configuration file
config.read('./config/config.ini')

# Accessing the configuration variables
GLOBAL_CONFIG = {
    'ipv4_address': config.get('network', 'ipv4_address'),
    'ipv4_adapter': config.get('network', 'ipv4_adapter'),
    'network_output_file': config.get('network', 'network_output_file'),
    'jinja_template_file': config.get('network', 'jinja_template_file'),
    'folder_to_archive': config.get('network', 'folder_to_archive'),
    'archive_path': config.get('network', 'archive_path'),
}

def archive_folder(folder_to_archive: str = GLOBAL_CONFIG['folder_to_archive'], archive_path: str = GLOBAL_CONFIG['archive_path']):
    folder_name = folder_to_archive.split('/')[-1]
    backup_path = f"{archive_path}/{folder_name}.bak"
    
    # if the folder doesnt exist, create it.
    if not os.path.exists(folder_to_archive):
        print(f"Folder '{folder_to_archive}' does not exist")
        os.makedirs(folder_to_archive)
        print(f"Folder '{folder_to_archive}' has been created")
    
    if os.path.exists(backup_path):
        shutil.rmtree(backup_path)
        print(f"Folder '{backup_path}' already exists and has been removed")
    shutil.copytree(folder_to_archive, backup_path)
    print(f"Folder '{folder_name}' has been archived as '{backup_path}'")
    
def restart_network_manager():
    os.system(f"nmcli con load {GLOBAL_CONFIG['network_output_file']}")
    os.system("systemctl restart NetworkManager")
    
def load_template(jinja_template_file: str) -> jinja2.Template:
    with open(jinja_template_file, 'r') as template_file:
        template_content = template_file.read()
        template = Template(template_content)
    return template

def write_template_to_file(template: jinja2.Template, output_file: str, **kwargs):
    rendered_template = template.render(**kwargs)
    with open(output_file, 'w') as file:
        file.write(rendered_template)
    print(f"Rendered template has been written to '{output_file}'")
    
def configure_networking(ipv4_address: str = GLOBAL_CONFIG['ipv4_address'], ipv4_adapter: str = GLOBAL_CONFIG['ipv4_adapter'], 
                        output_file: str = GLOBAL_CONFIG['network_output_file'], jinja_template_file: str =GLOBAL_CONFIG['jinja_template_file']):
    template = load_template(jinja_template_file)
    write_template_to_file(template, output_file, ipv4_address=ipv4_address, ipv4_adapter=ipv4_adapter)
    print(f"Network adapter '{ipv4_adapter}' has been configured with IPv4 address '{ipv4_address}")
    restart_network_manager()
    print(f"NetworkManager service has been restarted")
    
def main():
    archive_folder()
    configure_networking()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
