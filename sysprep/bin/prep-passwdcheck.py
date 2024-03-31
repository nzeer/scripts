import os
import configparser
from lib.libTemplateProcessing.libTemplateProcessing import TemplateProcessor 

#ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize the configparser
_config = configparser.ConfigParser()

# Read the configuration file
_config.read('../config/config.ini')

GLOBAL_CONFIG_PASSWDCHECK = {
    'passwdcheck_path': _config.get('passwdcheck', 'path'),
    'passwdcheck_jinja_template': _config.get('passwdcheck', 'jinja_template'),
    'passwdcheck_host_ip': _config.get('network', 'ipv4_address'),
    'passwdcheck_host_name': _config.get('hostname', 'hostname'),
}

def load_template(jinja_template_file: str) -> TemplateProcessor.jinja2.Template:
    """
    Load a Jinja template from a file.

    Args:
        jinja_template_file (str): The path to the Jinja template file.

    Returns:
        tp.jinja2.Template: The loaded Jinja template.
    """
    print(f"Attemping to load template from '{jinja_template_file}'")
    return TemplateProcessor.load_template(jinja_template_file)

def write_template_to_file(template: TemplateProcessor.jinja2.Template, output_file: str, **kwargs) -> bool:
    """
    Write a Jinja template to a file.

    Args:
        template (tp.jinja2.Template): The Jinja template to write.
        output_file (str): The path to the output file.
        **kwargs: Additional keyword arguments to pass to the template.

    Returns:
        bool: True if the template was successfully written to the file, False otherwise.
    """
    print(f"Attempting to write '{output_file}' using the provided template...")
    return TemplateProcessor.write_template_to_file(template, output_file, **kwargs)

def prep_passwdcheck(passwdcheck_path: str = GLOBAL_CONFIG_PASSWDCHECK['passwdcheck_path'], passwdcheck_jinja_template: str = GLOBAL_CONFIG_PASSWDCHECK['passwdcheck_jinja_template'], 
                    passwdcheck_host_ip: str = GLOBAL_CONFIG_PASSWDCHECK['passwdcheck_host_ip'],
                    passwdcheck_host_name: str = GLOBAL_CONFIG_PASSWDCHECK['passwdcheck_host_name']) -> bool:
    """
    Prepare the passwdcheck script by loading a Jinja template, filling it with the provided values, and writing it to a file.

    Args:
        passwdcheck_path (str): The path to the passwdcheck script file.
        passwdcheck_jinja_template (str): The path to the Jinja template file for passwdcheck.
        passwdcheck_host_ip (str): The IP address of the host.
        passwdcheck_host_name (str): The hostname of the host.

    Returns:
        bool: True if the passwdcheck script was successfully prepared, False otherwise.
    """
    template = load_template(passwdcheck_jinja_template)
    return write_template_to_file(template=template, output_file=passwdcheck_path, passwdcheck_host_ip=passwdcheck_host_ip, passwdcheck_host_name=passwdcheck_host_name)

def exec_passwdcheck():
    """
    Execute the passwdcheck script.
    """
    print(f"Running {GLOBAL_CONFIG_PASSWDCHECK['passwdcheck_path']} ...")
    os.system(f"sh {GLOBAL_CONFIG_PASSWDCHECK['passwdcheck_path']}")

def main():
    """
    The main function that prepares and executes the passwdcheck script.
    """
    if prep_passwdcheck():
        print(f"passwdcheck.sh has been configured for '{GLOBAL_CONFIG_PASSWDCHECK['passwdcheck_host_name']}' / '{GLOBAL_CONFIG_PASSWDCHECK['passwdcheck_host_ip']}'")
        exec_passwdcheck()
        print("Done.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")