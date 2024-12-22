# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

import subprocess


def run_checks() -> None:
    commands = [
        ["black", "src/hob"],
        ["flake8", "src/hob"],
        ["mypy", "src/hob"],
        ["pytest"],
    ]

    for command in commands:
        result = subprocess.run(command)
        if result.returncode != 0:
            print(f"Command {command} failed with return code {result.returncode}")
            break  # Stop running the next commands if one fails


if __name__ == "__main__":
    run_checks()
