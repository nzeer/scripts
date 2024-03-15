import os
import configparser
from jinja2 import Template
import jinja2

# Initialize the configparser
config = configparser.ConfigParser()

# Read the configuration file
config.read('config.ini')

GLOBAL_CONFIG_RSYSLOG = {
    'rsyslog_path': config.get('rsyslog', 'rsyslog_path'),
    'rsyslog_jinja_template': config.get('rsyslog', 'rsyslog_jinja_template'),
    'rsyslog_server_ip': config.get('rsyslog', 'rsyslog_server_ip'),
}

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

def prep_rsyslog_conf(rsyslog_conf: str = GLOBAL_CONFIG_RSYSLOG['rsyslog_path'], rsyslog_jinja_template: str = GLOBAL_CONFIG_RSYSLOG['rsyslog_jinja_template'], 
                    rsyslog_server_ip: str = GLOBAL_CONFIG_RSYSLOG['rsyslog_server_ip']):
    template = load_template(rsyslog_jinja_template)
    write_template_to_file(template, rsyslog_conf, rsyslog_server_ip=rsyslog_server_ip)
    print(f"Rsyslog has been configured to send logs to '{rsyslog_server_ip}'")

def restart_rsyslog():
    os.system("systemctl restart rsyslog")
    print("Rsyslog service has been restarted")
    
def main():
    prep_rsyslog_conf()
    restart_rsyslog()
    
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")