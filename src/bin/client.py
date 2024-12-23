#!/bin/env python
# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

import requests

API_URL = "http://127.0.0.1:8000"
# Mock token: In a real scenario, obtain this from /token
# For demonstration, let's first register and then login to get a token.
# Or we can assume we already have a token after running the steps manually.


def get_token(username: str, password: str) -> str:
    data = {"username": username, "password": password}
    resp = requests.post(f"{API_URL}/token", data=data)
    resp.raise_for_status()
    return resp.json()["access_token"]


def main():
    
    token = get_token("test", "meep")

    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/bundles", headers=headers)
    if resp.status_code == 200:
        bundles = resp.json()
        print("Bundles:", bundles)
    else:
        print("Failed to fetch bundles:", resp.status_code, resp.text)

    resp = requests.get(f"{API_URL}/chat", headers=headers)
    if resp.status_code == 200:
        response = resp.json()
        print("LLM Response:", response)
    else:
        print("Failed to fetch bundles:", resp.status_code, resp.text)


if __name__ == "__main__":
    main()
