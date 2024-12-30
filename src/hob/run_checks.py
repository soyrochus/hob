# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

import subprocess


def run_checks() -> None:
    commands = [
        ["black", "src/hob", "src/hobknob", "src/hobs"],
        ["flake8", "src/hob", "src/hobknob", "src/hobs"],
        ["mypy", "src/hob", "src/hobknob", "src/hobs"],
        ["pytest"],
    ]

    for command in commands:
        result = subprocess.run(command)
        if result.returncode != 0:
            print(f"Command {command} failed with return code {result.returncode}")
            break  # Stop running the next commands if one fails


def run_checks_ruff() -> None:
    commands = [
        ["ruff", "format"],
        ["ruff", "check", "src", "--fix"],
        ["mypy", "src/hob", "src/hobknob", "src/hobs"],
        ["pytest"],
    ]

    for command in commands:
        result = subprocess.run(command)
        if result.returncode != 0:
            print(f"Command {command} failed with return code {result.returncode}")
            break  # Stop running the next commands if one fails


if __name__ == "__main__":
    run_checks()
