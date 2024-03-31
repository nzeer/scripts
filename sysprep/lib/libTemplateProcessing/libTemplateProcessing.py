from jinja2 import Template
import jinja2

class TemplateProcessor:
    @staticmethod
    def load_template(jinja_template_file: str) -> jinja2.Template:
        """
        Load a Jinja template from a file.

        Args:
            jinja_template_file (str): The path to the Jinja template file.

        Returns:
            jinja2.Template: The loaded Jinja template.
        """
        with open(jinja_template_file, 'r') as template_file:
            template_content = template_file.read()
            template = Template(template_content)
        return template

    @staticmethod
    def write_template_to_file(template: jinja2.Template, output_file: str, **kwargs) -> bool:
        """
        Render a Jinja template and write it to a file.

        Args:
            template (jinja2.Template): The Jinja template to render.
            output_file (str): The path to the output file.
            **kwargs: Keyword arguments to pass to the template.

        Returns:
            bool: True if the template was successfully rendered and written to the file, False otherwise.
        """
        result = False
        rendered_template = template.render(**kwargs)
        with open(output_file, 'w') as file:
            file.write(rendered_template)
            result = True
            print(f"Rendered template has been written to '{output_file}'")
        return result
