# Copyright © 2025, MIT License, Author: Iwan van der Kleijn 
# Hob: A private AI-augmented workspace for project notes and files.

import requests

API_URL = "http://127.0.0.1:8000"
# Mock token: In a real scenario, obtain this from /token
# For demonstration, let's first register and then login to get a token.
# Or we can assume we already have a token after running the steps manually.

def get_token(email: str, password: str) -> str:
    data = {"username": email, "password": password}
    resp = requests.post(f"{API_URL}/token", data=data)
    resp.raise_for_status()
    return resp.json()["access_token"]


def main():
    # Register a user if not already done
    # Normally you'd handle errors, duplicates, etc.
    try:
        r = requests.post(f"{API_URL}/register", json={
            "name": "John Doe",
            "email": "johndoe@example.com",
            "age": 30,
            "password": "secret"
        })
        if r.status_code == 201:
            print("User registered.")
        else:
            print("User already registered or other issue:", r.text)
    except:
        pass

    token = get_token("johndoe@example.com", "secret")

    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/bundles", headers=headers)
    if resp.status_code == 200:
        bundles = resp.json()
        print("Bundles:", bundles)
    else:
        print("Failed to fetch bundles:", resp.status_code, resp.text)


if __name__ == "__main__":
    main()
