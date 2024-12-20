# Copyright © 2025, MIT License, Author: Iwan van der Kleijn 
# Hob: A private AI-augmented workspace for project notes and files.

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BundleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
