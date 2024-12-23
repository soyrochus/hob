# Hob

**Hob** is a private, AI-augmented workspace for organizing, searching, and conversing with your project notes and files. It enables you to work with mixed datasets from different sources, configure custom prompt templates, and integrate plugable agents—all through a simple object model, API, and (ultimately) user interface.

[A **hob** is a small, mythological household spirit from English folklore](https://en.wikipedia.org/wiki/Hob_(folklore)), known for helping with chores—unless offended, in which case they become a nuisance. Similarly, Hob the app is your friendly, AI-powered assistant, organizing and managing your project notes and files. Treat it well, and it’ll work wonders; ignore it, and your tasks might just pile up!

![Hob](images/hob.png)

## Key Features
- Seamlessly organize documents, notes, and other artifacts into “Bundles” for project-based management.
- Configure and manage mixed datasets from various sources with ease.
- Define and use custom prompt templates for tailored AI interactions.
- Extend functionality with plugable agents for custom workflows.
- Vector-based embeddings enable rich semantic search and context-driven Q&A.
- Designed for extensibility through a clean object model and API.

---

## Installation

### Using Poetry (Recommended)
Hob uses [Poetry](https://python-poetry.org/) for dependency management. Follow these steps to set up the project:

1. Install Poetry:
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

4. And then launch the service...


### Launching the Service
Run the Hob server with the following options:
```bash
python -m app.main [options]
```
Available options:
- `-c`, `--config`: Path to the TOML configuration file (default: `hob-config.toml`).
- `--host`: Host to bind the server (default: `127.0.0.1`).
- `--port`: Port to bind the server (default: `8000`).
- `--reload`: Enable auto-reload for development.
- `--log-level`: Set the logging level (default: `info`).

Example:
```bash
python -m app.main --config custom-config.toml --host 0.0.0.0 --port 8080 --reload
```

---

## Testing
To ensure code quality and functionality:

- Run unit tests with:
  ```bash
  pytest
  ```

- Run all checks (linting, type checks, and tests) in one go:
  ```bash
  poetry run check-all
  ```

---

## Notes
- Hob is an early prototype designed for extensibility and modularity.
- Future plans include a UI for managing datasets, agents, and configurations.

---

## Copyright and License

Copyright (c) 2025 Iwan van der Kleijn  
License: MIT License  

For the full license text, see the LICENSE file in the root of the project.

