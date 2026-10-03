#!/usr/bin/env python3
"""Generate docs/API_REFERENCE.md from backend/openapi.json.

Keep the schema and the reference in sync:

    cd backend && python dump_openapi.py
    cd .. && python scripts/generate_api_docs.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "backend" / "openapi.json"
OUTPUT_PATH = ROOT / "docs" / "API_REFERENCE.md"

METHODS = ("get", "post", "put", "patch", "delete")


def type_name(schema):
    """A short, human-readable name for a JSON schema fragment."""
    if not schema:
        return "any"
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if "anyOf" in schema:
        return " | ".join(type_name(part) for part in schema["anyOf"])
    if "allOf" in schema:
        return " & ".join(type_name(part) for part in schema["allOf"])
    kind = schema.get("type", "object")
    if kind == "array":
        return f"array<{type_name(schema.get('items'))}>"
    fmt = schema.get("format")
    return f"{kind} ({fmt})" if fmt else kind


def render_parameters(operation):
    parameters = operation.get("parameters", [])
    if not parameters:
        return []
    lines = [
        "| Name | In | Required | Type | Description |",
        "| --- | --- | --- | --- | --- |",
    ]
    for parameter in parameters:
        lines.append(
            "| `{name}` | {location} | {required} | {type} | {description} |".format(
                name=parameter["name"],
                location=parameter["in"],
                required="yes" if parameter.get("required") else "no",
                type=type_name(parameter.get("schema")),
                description=(parameter.get("description") or "").replace("\n", " "),
            )
        )
    return lines


def render_request_body(operation):
    body = operation.get("requestBody")
    if not body:
        return []
    content = body.get("content", {})
    media = next(iter(content), "application/json")
    schema = content.get(media, {}).get("schema")
    required = "required" if body.get("required") else "optional"
    return [f"Request body ({media}, {required}): `{type_name(schema)}`", ""]


def render_responses(operation):
    responses = operation.get("responses", {})
    if not responses:
        return []
    lines = ["| Status | Description |", "| --- | --- |"]
    for status, response in responses.items():
        lines.append(f"| {status} | {response.get('description', '')} |")
    return lines


def render_endpoint(method, path, operation):
    lines = [f"#### `{method.upper()} {path}`", ""]
    summary = operation.get("summary") or operation.get("operationId") or ""
    if summary:
        lines += [summary, ""]
    description = operation.get("description")
    if description and description != summary:
        lines += [description.strip(), ""]

    lines += render_request_body(operation)
    lines += render_parameters(operation)
    if operation.get("parameters"):
        lines.append("")
    lines += render_responses(operation)
    lines.append("")
    return lines


def main():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    info = schema.get("info", {})

    grouped = {}
    for path, methods in schema.get("paths", {}).items():
        for method in METHODS:
            operation = methods.get(method)
            if not operation:
                continue
            tags = operation.get("tags") or ["default"]
            grouped.setdefault(tags[0], []).append((method, path, operation))

    out = [
        "# API Reference",
        "",
        f"Generated from `backend/openapi.json` ({info.get('title', 'API')} "
        f"v{info.get('version', '')}). Do not edit by hand; regenerate with "
        "`scripts/generate_api_docs.py`.",
        "",
    ]

    out += [
        "## Authentication",
        "",
        "Most endpoints require a session token obtained from "
        "`POST /api/v1/auth/login`. Two transports are accepted:",
        "",
        "- `Authorization: Bearer <session_id>` header (used by the SPA/API clients).",
        "- `miniui_session` HttpOnly cookie (set by login; used by rendered pages).",
        "",
        "Mutating requests that are not form posts must also send "
        "`X-Requested-With: XMLHttpRequest` (CSRF protection). `/docs`, "
        "`/openapi.json`, the auth endpoints and runtime page posts are exempt.",
        "",
        "Interactive documentation is served at `/docs` (Swagger UI) and "
        "`/redoc`.",
        "",
    ]

    out += ["## Endpoint Index", ""]
    for tag in sorted(grouped):
        out.append(f"### {tag}")
        out.append("")
        out.append("| Method | Path | Summary |")
        out.append("| --- | --- | --- |")
        for method, path, operation in grouped[tag]:
            summary = (operation.get("summary") or "").replace("|", "\\|")
            out.append(f"| {method.upper()} | `{path}` | {summary} |")
        out.append("")

    out += ["## Endpoint Details", ""]
    for tag in sorted(grouped):
        out += [f"### {tag}", ""]
        for method, path, operation in sorted(grouped[tag], key=lambda item: item[1]):
            out += render_endpoint(method, path, operation)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
