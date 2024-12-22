# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

from datetime import datetime
from sqlalchemy import Column, DateTime, String, Table, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .db import Base

from enum import Enum

# Utility types


class ArtifactType(Enum):
    TEXT = "text"  # Represents plain text records or templates
    MARKDOWN = "markdown"  # Represents markdown files
    FILE = "file"  # Generic file
    ZIP = "zip"  # Compressed archives
    URL = "url"  # External resources like websites
    GITHUB = "github"  # GitHub repositories
    PROMPT_TEMPLATE = "prompt-template"  # Prompt templates for AI models

    def __str__(self):
        return self.value

    @staticmethod
    def from_string(value: str):
        """
        Convert a string to an ArtifactType.
        Raises ValueError if the value is invalid.
        """
        try:
            return ArtifactType(value)
        except ValueError:
            raise ValueError(
                f"Invalid ArtifactType: {value}. Valid types are: {', '.join(t.value for t in ArtifactType)}"
            )


# Association Table for Many-to-Many Relationship
user_bundle = Table(
    "user_bundle",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id"), primary_key=True),
    Column("bundle_id", String, ForeignKey("bundles.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)

    # Relationship with Bundles
    bundles = relationship("Bundle", secondary=user_bundle, back_populates="users")


class Bundle(Base):
    __tablename__ = "bundles"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)

    # Relationship with Users
    users = relationship("User", secondary=user_bundle, back_populates="bundles")
    artifacts = relationship(
        "Artifact", back_populates="bundle", cascade="all, delete-orphan"
    )
    conversations = relationship(
        "Conversation", back_populates="bundle", cascade="all, delete-orphan"
    )


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # E.g., "text", "zip", "file", "url"
    origin = Column(String, nullable=False)  # Pointer to the data's source
    attributes = Column(JSON, nullable=True)  # Additional attributes
    date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Foreign key
    bundle_id = Column(String, ForeignKey("bundles.id"), nullable=False)

    # Relationships
    bundle = relationship("Bundle", back_populates="artifacts")
    elements = relationship(
        "Element", back_populates="artifact", cascade="all, delete-orphan"
    )


class Element(Base):
    __tablename__ = "elements"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    namespace = Column(String, nullable=False)  # Location or identifier of the element
    content = Column(Text, nullable=True)  # Textual content of the element

    # Foreign key
    artifact_id = Column(String, ForeignKey("artifacts.id"), nullable=False)

    # Relationships
    artifact = relationship("Artifact", back_populates="elements")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)

    # Foreign key
    bundle_id = Column(String, ForeignKey("bundles.id"), nullable=False)

    # Relationships
    bundle = relationship("Bundle", back_populates="conversations")
    interactions = relationship(
        "Interaction", back_populates="conversation", cascade="all, delete-orphan"
    )


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(String, primary_key=True)
    prompt = Column(Text, nullable=False)  # User's question
    response = Column(Text, nullable=False)  # AI's answer

    # Foreign key
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="interactions")
