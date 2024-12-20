# Hob

**Hob** is a private, AI-augmented workspace for organizing, searching, and conversing with your project notes and files. It groups your documents, notes, conversations, and other artifacts into “Bundles,” then applies vector-based embeddings for rich semantic search and retrieval.

**Features:**
- Create and manage Bundles (projects) containing text notes and files.
- Asynchronous Jobs for file ingestion, embedding, and search indexing.
- JWT-based user authentication with protected endpoints.
- Vector database integration for semantic search and context-driven Q&A.

See: [Hob specifications](doc/hob-specification.md) but note that this is very much a draft aka in a preliminary stage



---

## Installation Options

### Option 1: Using Poetry (Recommended)
[Poetry](https://python-poetry.org/) is a modern dependency management tool for Python projects. If you already use Poetry:

1. Install Poetry if you don’t have it:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

4. Run the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

---

### Option 2: Using pip
If you cannot use Poetry, install dependencies with pip:

1. Install dependencies from the `requirements.txt` file:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

---

### Notes
- Using Poetry provides better dependency resolution and a dedicated virtual environment for the project.
- For organizations restricted to `pip`, the `requirements.txt` file includes an identical list of dependencies.



**Quick Start:**
1. Run the FastAPI server (e.g. `uvicorn app.main:app --reload` or the scripts in the bin/ directory).
2. Register a user, log in to obtain a token.
3. Access protected endpoints with your JWT token.

**Notes:**
- This is an early, skeletal prototype designed for extensibility and modularity.
- For the client, a simple Python script (`client.py`) can query the service.

## Copyright and License

Copyright (c) 2025 Iwan van der Kleijn

License: MIT License

For the full license text, please refer to the LICENSE file in the root of the project.
