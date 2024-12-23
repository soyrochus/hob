# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.


from jinja2 import Template


def load_template(template_path):
    """Load the prompt template from the file."""

    if template_path:

        with open(template_path, "r") as file:
            return file.read()

    else:
        return """You are an AI assistent. You are an expert in the topic the user requests info about.
Respond concisely but completely without leaving detail. Explain the "why" of your choices.
This is the user prompt:

{{ user_prompt }}

"""


def render_template(template_content, variables):
    """Render the template with the provided variables."""
    template = Template(template_content)
    return template.render(**variables)
