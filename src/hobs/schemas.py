# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.
# Hobs is the API service for Hob. It provides a simple interface to the Hob API.

# Data Value Object

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


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
    bundleid: int
    conversation_id: int

class ChatRequest(BaseModel):

    message: str
    bundleid: int
    conversation_id: Optional[int] = None