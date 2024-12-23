# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.


# Data Value Object

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserData(BaseModel):
    id: int
    login: str
    name: str
    email: str


class BundleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime

class ChatResponse(BaseModel):

    message: str
