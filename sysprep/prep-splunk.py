import shutil
import os
import configparser
from jinja2 import Template
import jinja2

# Initialize the configparser
config = configparser.ConfigParser()

# Read the configuration file
config.read('config.ini')

# Accessing the configuration variables
GLOBAL_CONFIG = {
    'splunk_archive_src': config.get('splunk', 'splunk_archive_src'),
    'splunk_archive_path': config.get('splunk', 'splunk_archive_path'),
    'splunk_jinja_inputs': config.get('splunk', 'splunk_jinja_inputs'),
    'splunk_jinja_server': config.get('splunk', 'splunk_jinja_server'),
    'splunk_bin_path': config.get('splunk', 'splunk_bin_path'),
    'splunk_hostname': config.get('hostname', 'hostname'),
    'splunk_server_path': config.get('splunk', 'splunk_server_path'),
    'splunk_inputs_path': config.get('splunk', 'splunk_inputs_path'),
    
}

def archive_folder(folder_to_archive: str = GLOBAL_CONFIG['splunk_archive_src'], archive_path: str = GLOBAL_CONFIG['splunk_archive_path']):
    folder_name = folder_to_archive.split('/')[-1]
    backup_path = f"{archive_path}/{folder_name}.bak"
    shutil.copytree(folder_to_archive, backup_path)
    print(f"Folder '{folder_name}' has been archived as '{backup_path}'")
    
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
    
def configure_splunk_server_conf(hostname: str = GLOBAL_CONFIG['splunk_hostname'], jinja_template_file: str = GLOBAL_CONFIG['splunk_jinja_server'], 
                                output_file: str = GLOBAL_CONFIG['splunk_server_path']):
    template = load_template(jinja_template_file)
    write_template_to_file(template, output_file, splunk_hostname=hostname)
    print(f"Splunk server.conf has been configured with hostname '{hostname}'")
    
def configure_splunk_inputs_conf(hostname: str = GLOBAL_CONFIG['splunk_hostname'], jinja_template_file: str = GLOBAL_CONFIG['splunk_jinja_inputs'], 
                                output_file: str = GLOBAL_CONFIG['splunk_inputs_path']):
    template = load_template(jinja_template_file)
    write_template_to_file(template, output_file, splunk_hostname=hostname)
    print(f"Splunk inputs.conf has been configured with hostname '{hostname}'")
    
def enable_splunk_service(splunk_bin: str = GLOBAL_CONFIG['splunk_bin_path']):
    os.system(f"{splunk_bin} enable boot-start")
    print("Splunk service has been enabled to start on boot")
    
def main():
    archive_folder()
    configure_splunk_server_conf()
    configure_splunk_inputs_conf()
    enable_splunk_service()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")