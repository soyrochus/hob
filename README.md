# Hob: The Bicameral Agent

Hob is now a lightweight framework for building **bicameral agents** in Python. A planner turns a text goal into a JSON plan and an executor walks that plan using pluggable primitive tools.

## What is a Bicameral Agent?

A **bicameral agent** in AI is an architecture that separates “planning” (deliberate decision-making) from “execution” (rapid, mechanical action). It typically consists of:

* **Orchestrator/Planner**: Interprets the user’s intent, decomposes it into steps, and produces a structured plan.
* **Executor(s)/Task Agents**: Carry out the steps, often by invoking specific tools or functions.

This mirrors the **theory of bicameral cognition** (Julian Jaynes, *The Origin of Consciousness in the Breakdown of the Bicameral Mind*), which proposed that the ancient human mind operated with two “chambers”:

1. One “speaks” (issues instructions—like the Planner),
2. The other “acts” (obeys the instructions—like the Executor),
   with no introspective consciousness linking them.

In AI, **bicameral agents** operationalize this by cleanly dividing *planning* and *doing*, enabling more robust, auditable, and modular intelligent systems.

## And "Hob"?

[A **hob** is a small, mythological household spirit from English folklore](https://en.wikipedia.org/wiki/Hob_(folklore)), known for helping with chores—unless offended, in which case they become a nuisance. Similarly, Hob the app is your friendly, AI-powered assistant, organizing and managing your project notes and files. Treat it well, and it’ll work wonders; ignore it, and your tasks might just pile up!

![Hob](images/hob.png)

## Setup

```bash
uv sync
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


## Copyright and License

Copyright (c) 2025 Iwan van der Kleijn  
License: MIT License  

For the full license text, see the LICENSE file in the root of the project.

