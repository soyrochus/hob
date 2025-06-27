"""JSON-Schema definitions for planner primitives."""

SEARCHER_SCHEMA = {
    "type": "object",
    "required": ["query", "top_k"],
    "properties": {
        "query": {"type": "string"},
        "top_k": {"type": "integer", "minimum": 1, "maximum": 20},
    },
}

FETCHER_SCHEMA = {
    "type": "object",
    "required": ["url"],
    "properties": {
        "url": {"type": "string", "format": "uri"},
    },
}

PARSER_SCHEMA = {
    "type": "object",
    "required": ["raw", "schema"],
    "properties": {
        "raw": {"$ref": "#/definitions/Pointer"},
        "schema": {
            "type": "object",
            "patternProperties": {
                "^[a-zA-Z0-9_]+$": {
                    "type": "string",
                    "pattern": "^(css:|xpath:|regex:).+$",
                }
            },
        },
    },
}

COMPUTE_SCHEMA = {
    "type": "object",
    "required": ["op", "inputs"],
    "properties": {
        "op": {
            "type": "string",
            "enum": [
                "normalize_prices",
                "margin_calculation",
                "filter",
                "sort",
                "merge",
            ],
        },
        "inputs": {"type": "array", "items": {"$ref": "#/definitions/Pointer"}},
        "params": {"type": "object"},
    },
}

STORE_SCHEMA = {
    "type": "object",
    "required": ["action", "key"],
    "properties": {
        "action": {"type": "string", "enum": ["write", "read"]},
        "key": {"type": "string"},
    },
}

POINTER_SCHEMA = {
    "type": "object",
    "required": ["from", "field"],
    "properties": {
        "from": {"type": "integer", "minimum": 0},
        "field": {"type": "string"},
    },
}

MASTER_SCHEMA = {
    "type": "array",
    "items": {
        "oneOf": [
            SEARCHER_SCHEMA,
            FETCHER_SCHEMA,
            PARSER_SCHEMA,
            COMPUTE_SCHEMA,
            STORE_SCHEMA,
        ]
    },
    "definitions": {"Pointer": POINTER_SCHEMA},
}
