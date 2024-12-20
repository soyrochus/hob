# Hob

**Hob** is a private, AI-augmented workspace for organizing, searching, and conversing with your project notes and files. It groups your documents, notes, conversations, and other artifacts into “Bundles,” then applies vector-based embeddings for rich semantic search and retrieval.

**Features:**
- Create and manage Bundles (projects) containing text notes and files.
- Asynchronous Jobs for file ingestion, embedding, and search indexing.
- JWT-based user authentication with protected endpoints.
- Vector database integration for semantic search and context-driven Q&A.

See: [Hob specifications](doc/hob-specification.md) but note that this is very much a draft aka in a preliminary stage

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
