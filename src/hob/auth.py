# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

import base64
import logging
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError


ph = PasswordHasher()

logger = logging.getLogger(__name__)


def encode_hash(hash_string):
    """Encodes the hash in base64 to avoid special character issues."""
    return base64.urlsafe_b64encode(hash_string.encode("utf-8")).decode("utf-8")


def decode_hash(encoded_hash):
    """Decodes a base64-encoded hash."""
    return base64.urlsafe_b64decode(encoded_hash.encode("utf-8")).decode("utf-8")


def hash_password(password, base64: bool = False):
    """Hashes a password using Argon2."""
    raw_hash = ph.hash(password.strip())
    if base64:
        return encode_hash(raw_hash)
    else:
        return raw_hash


def validate_password(password, given_hash, base64: bool = False):
    """Validates a password against the hashed value."""
    try:
        if base64:
            original_hash = decode_hash(given_hash.strip())
        else:
            original_hash = given_hash.strip()

        ph.verify(original_hash, password.strip())
        return True
    except VerifyMismatchError:
        return False
    except InvalidHashError as e:
        logger.error(f"Invalid hash: {e}, hash: {original_hash}")
        raise e
