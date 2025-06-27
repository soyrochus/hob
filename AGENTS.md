You are an advanced Python code‑generation assistant.

╔════════════════════════════════════════════════════════════════╗
║                    HIGH‑LEVEL OBJECTIVE                       ║
╚════════════════════════════════════════════════════════════════╝
Instead of the current project - Hob - Generate a fully runnable **bicameral agent framework** that:

1. **Plans** – A “Planner” LLM turns a user goal into a JSON‑AST plan built only from a fixed set of generic primitives.
2. **Executes** – An “Executor” walks that AST, resolves pointers, and calls the primitives.
3. **Evolves** – All components are decoupled by abstract interfaces so new primitives or planner strategies can be plugged in.

╔════════════════════════════════════════════════════════════════╗
║                  GLOBAL TECHNICAL CONSTRAINTS                 ║
╚════════════════════════════════════════════════════════════════╝
• Language         : Python 3.11  
• Packaging        : **pyproject.toml** + **setuptools**  
• Lint & typing    : `ruff` + `mypy` (strict)  
• External libs    : `requests`, `beautifulsoup4`, `lxml`, `jsonschema`, `rich` (CLI pretty‑print)  
• No other third‑party dependencies; standard library wherever possible.  
• Every public class/function is fully type‑hinted *and* contains a PEP‑257 docstring.

╔════════════════════════════════════════════════════════════════╗
║                    PROJECT TREE & FILE ROLES                  ║
╚════════════════════════════════════════════════════════════════╝
bicameral_agent/             # top‑level package  
├─ agent_context.py          # dataclass holding user msg, memory snapshot, metadata  
├─ core/  
│  ├─ interfaces.py          # abstract ABCs: Tool, Memory, Planner, Executor  
│  ├─ registry.py            # ToolRegistry: add/get tools, singleton accessor  
│  └─ exceptions.py          # PlanValidationError, ExecutionError …  
├─ planner/  
│  ├─ schemas.py             # JSON‑Schema objects for primitives + master schema  
│  ├─ dsl.py                 # Pointer dataclass + helper functions  
│  └─ planner.py             # Concrete DSLPlanner: NL goal ➜ validated plan  
├─ executor/  
│  └─ executor.py            # AST executor (resolves pointers, calls tools, traces)  
├─ tools/                     # one module per primitive  
│  ├─ __init__.py            # auto‑register all primitives into ToolRegistry  
│  ├─ searcher.py            # stub search (returns mock URLs or uses DuckDuckGo HTML)  
│  ├─ fetcher.py             # HTTP GET raw HTML (requests)  
│  ├─ parser.py              # css:/xpath:/regex: extraction (BeautifulSoup + lxml)  
│  ├─ compute.py             # normalize_prices, margin_calculation, filter, sort, merge  
│  └─ store.py               # in‑memory dict store (future swap for Redis)  
├─ memory/                    # simple vector & buffer memory placeholders  
│  └─ in_memory.py           # not essential for MVP but interface demo  
├─ samples/  
│  ├─ car_arbitrage.py       # CLI demo: accepts “--goal” arg, prints JSON result  
│  └─ repl.py                # tiny REPL to enter goals interactively  
├─ tests/                     # pytest suite covering plan validation & executor paths  
│  ├─ test_schemas.py  
│  └─ test_car_arbitrage.py  
├─ pyproject.toml            # dependencies, scripts, tool configs  
└─ README.md                 # usage, architecture, adding new tools

╔════════════════════════════════════════════════════════════════╗
║                 DOMAIN‑SPECIFIC LANGUAGE (DSL)                ║
╚════════════════════════════════════════════════════════════════╝
Each AST node is:
```python
{
  "step": "unique_snake_case_id",
  "with": "Searcher|Fetcher|Parser|Compute|Store",
  "args": { ... }                      # must match schema below
}
````

`Pointer` = `{ "from": <int>, "field": "<dot/bracket path or empty for whole>" }`

### Primitive JSON‑Schemas (to embed in planner/schemas.py)

1. **Searcher**

```json
{ "type":"object",
  "required":["query","top_k"],
  "properties":{
    "query":{"type":"string"},
    "top_k":{"type":"integer","minimum":1,"maximum":20}
}}
```

2. **Fetcher**

```json
{ "type":"object",
  "required":["url"],
  "properties":{
    "url":{"type":"string","format":"uri"}
}}
```

3. **Parser**

```json
{ "type":"object",
  "required":["raw","schema"],
  "properties":{
    "raw":{"$ref":"#/definitions/Pointer"},
    "schema":{
      "type":"object",
      "patternProperties":{
        "^[a-zA-Z0-9_]+$":{
          "type":"string","pattern":"^(css:|xpath:|regex:).+$"
}}}}}
```

4. **Compute**

```json
{ "type":"object",
  "required":["op","inputs"],
  "properties":{
    "op":{"type":"string","enum":["normalize_prices","margin_calculation",
                                  "filter","sort","merge"]},
    "inputs":{"type":"array","items":{"$ref":"#/definitions/Pointer"}},
    "params":{"type":"object"}
}}
```

5. **Store**

```json
{ "type":"object",
  "required":["action","key"],
  "properties":{
    "action":{"type":"string","enum":["write","read"]},
    "key":{"type":"string"}
}}
```

6. **definitions.Pointer**

```json
{ "type":"object",
  "required":["from","field"],
  "properties":{
    "from":{"type":"integer","minimum":0},
    "field":{"type":"string"}
}}
```

The master schema is an **array** where every item is `oneOf` the five schemas above.

╔════════════════════════════════════════════════════════════════╗
║                      IMPLEMENTATION NOTES                     ║
╚════════════════════════════════════════════════════════════════╝
• **DSLPlanner** (`planner/planner.py`)
– Uses simple rule‑based decomposition: search→fetch→parse per market, then compute.
– Validates the plan with `jsonschema.validate`; on error raises `PlanValidationError`.

• **Executor** (`executor/executor.py`)
– Iterates over the list; each result appended to `trace` list.
– `resolve_pointer(pointer, trace)` handles nested “field” paths with `jmespath`‑style traversal (implement manually; no extra lib).
– Comprehensive logging via `logging` + optional `--debug` CLI flag.

• **Compute Tool** (`tools/compute.py`)
– `normalize_prices`: strip currency symbols, convert to `float`.
– `margin_calculation`: expects two lists of dicts (`buy_market`, `sell_market`).
– `filter`, `sort`, `merge` are generic DataFrame‑like ops implemented with pure Python.

• **Samples**
– `car_arbitrage.py` loads a hard‑coded goal if none provided, runs Planner → Executor, pretty‑prints result with `rich`.
– Network calls *may* be stubbed/mocked to keep tests deterministic.

• **Tests**
– `test_schemas.py`: feed crafted bad plans, expect `PlanValidationError`.
– `test_car_arbitrage.py`: monkeypatch Searcher & Fetcher to return fixtures; assert final margin > 0.

• the existing **README.md** must overide completely the existing content but

YOU MUST preserve the name "Hob" and adjust the message. Hob is now the Bicameral agent. cover: setup, running samples, DSL spec, how to add a new primitive tool in three steps.

* use pyproject.toml for adding the required dependencies. Remove those which are not necessary

* use cli interface. Remove all web UI related items. 


