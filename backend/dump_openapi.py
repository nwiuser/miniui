"""Dump the OpenAPI schema to backend/openapi.json.

The frontend contract test reads this file, so the two sides cannot drift
without a test failing. Regenerate with:

    python dump_openapi.py
"""
import json
import os

from main import app

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "openapi.json")

with open(OUTPUT, "w", encoding="utf-8") as handle:
    json.dump(app.openapi(), handle, indent=2, sort_keys=True)

print(f"Wrote {OUTPUT}")
