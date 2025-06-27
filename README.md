# Hob: The Bicameral Agent

Hob is now a lightweight framework for building **bicameral agents** in Python. A planner turns a text goal into a JSON plan and an executor walks that plan using pluggable primitive tools.

## Setup

```bash
pip install -e .
```

## Running the Samples

```bash
python samples/car_arbitrage.py --goal "find car deals"
python samples/repl.py
```

## DSL Specification

Each plan step is an object with these fields:

```json
{
  "step": "unique_snake_case_id",
  "with": "Searcher|Fetcher|Parser|Compute|Store",
  "args": {"...": "as defined in schemas"}
}
```

Pointers reference previous results:

```json
{ "from": <int>, "field": "a.b[0]" }
```

See `hob/planner/schemas.py` for full primitive schemas.

## Adding a New Primitive Tool

1. Create a class inheriting `Tool` and implement `run`.
2. Add the class to `hob/tools/__init__.py` for auto‑registration.
3. Update planner logic and schemas if the primitive requires new arguments.
