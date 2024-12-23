#!/bin/env python
# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.


import argparse
from hob.auth import hash_password, validate_password


def main():
    parser = argparse.ArgumentParser(
        description="Hash or validate a password using Argon2."
    )
    parser.add_argument("password", help="The password to hash or validate.")
    parser.add_argument("-b", "--base64", action="store_true", help="Use base64 encoding/decoding")
    parser.add_argument(
        "-v",
        "--validate",
        nargs=1,
        metavar="ENCODED_HASH",
        help="Validate the given password against a base64-encoded hash.",
    )

    args = parser.parse_args()

    if args.validate:
        unprocessed_hash = args.validate[0]  # Get the unprocessed hash
        is_valid = validate_password(args.password, unprocessed_hash, args.base64)
        if is_valid:
            print("Password is valid.")
        else:
            print("Password is invalid.")
    else:
        hashed_password = hash_password(args.password, args.base64)
        if args.base64:
            print(f"Base64-encoded hashed password: {hashed_password}")
        else:
            print(f"Unencoded hashed password: {hashed_password}")


if __name__ == "__main__":
    main()
