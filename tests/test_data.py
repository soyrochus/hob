# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

from hob.models import ArtifactType


def test_articfact_type():
    assert str(ArtifactType.GITHUB) == "github"
  
    prompt_template = ArtifactType.from_string("prompt-template")
    assert str(prompt_template) == "prompt-template"
    assert prompt_template is ArtifactType.PROMPT_TEMPLATE
    
