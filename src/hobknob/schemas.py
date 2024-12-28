# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.
# Hobknob is the cli tool for using and managing the Hob appllication server
# from the command line. It provides a simple interface to the Hob API.


from pydantic import BaseModel


class Response(BaseModel):

    message: str


class Token(BaseModel):
    access_token: str
    token_type: str
