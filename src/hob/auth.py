# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

from typing import Protocol


class Authentication(Protocol):
    def authenticate(self, username: str, password: str) -> bool: ...


class DBAuthentication(Authentication):
    def __init__(self, db):
        self.db = db

    def authenticate(self, username: str, password: str) -> bool:
        return False
