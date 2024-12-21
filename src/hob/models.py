# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

from datetime import datetime
from sqlalchemy import Column, DateTime, String, Text
from .db import Base

# Database Models (Entities)


class Bundle(Base):
    __tablename__ = "bundles"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
