# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.
# Hobknob is the cli tool for using and managing the Hob appllication server
# from the command line. It provides a simple interface to the Hob API.


from hobknob.commands import parse_and_execute
import hobknob.bundles  # noqa:
import hobknob.auth  # noqa:


def main():
    parse_and_execute(program_name="hobknob", program_description="Hobknob CLI")


if __name__ == "__main__":
    main()
