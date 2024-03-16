import os
import configparser
from jinja2 import Template, Environment, FileSystemLoader
import jinja2
import yaml

# Initialize the configparser
config = configparser.ConfigParser()

# Read the configuration file
config.read('./config/config.ini')

GLOBAL_CONFIG_HOSTS = {
    'hosts_path': config.get('hosts', 'hosts_path'),
    'hosts_jinja_template': config.get('hosts', 'hosts_jinja_template'),
    'hosts_list_path': config.get('hosts', 'hosts_list_path')
}

def load_template(jinja_template_file: str) -> jinja2.Template:
    with open(jinja_template_file, 'r') as template_file:
        template_content = template_file.read()
        template = Template(template_content)
    return template

def write_template_to_file(template: jinja2.Template, output_file: str, rendered_hosts: str):
    # To save to a file, you could use:
    with open(output_file, 'w') as f:
        f.write(rendered_hosts)
    print(f"Rendered template has been written to '{output_file}'")
    
def load_hosts_list(hosts_list: str = GLOBAL_CONFIG_HOSTS['hosts_list_path']) -> dict:
    hosts_inventory: dict = {"hosts": {}}
    if not os.path.exists(hosts_list):
        print(f"Hosts list file '{hosts_list}' does not exist")
        return hosts_inventory
    with open(hosts_list, 'r') as file:
        hosts_inventory = yaml.safe_load(file)
    return hosts_inventory

def prep_hosts_file(hosts_path: str = GLOBAL_CONFIG_HOSTS['hosts_path'], 
                    hosts_jinja_template: str = GLOBAL_CONFIG_HOSTS['hosts_jinja_template'],
                    hosts_list: str = GLOBAL_CONFIG_HOSTS['hosts_list_path']):
    hosts_inventory = load_hosts_list(hosts_list)

    # Load the Jinja template
    # Assuming your Jinja template is stored in a file named 'hosts_template.j2'
    # in the same directory as this script.
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template(GLOBAL_CONFIG_HOSTS['hosts_jinja_template'])

    # Render the template with the hosts inventory
    rendered_hosts = template.render(hosts=hosts_inventory['hosts'])
    
    #template = load_template(hosts_jinja_template)
    write_template_to_file(template, hosts_path, rendered_hosts=rendered_hosts)
    print(f"Hosts file has been configured")
    
def main():
    prep_hosts_file()
    
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")