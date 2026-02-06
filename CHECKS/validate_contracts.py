#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRECISION_SCHEMA = ROOT / "CONTRACTS" / "precision_contract.schema.json"
ERROR_SCHEMA = ROOT / "CONTRACTS" / "error_response.schema.json"

REQUIRED_PROPERTIES = ["value", "confidence", "candidates", "method", "limits"]
REQUIRED_REQUIRED = ["confidence", "method", "limits"]

ERROR_REQUIRED_PROPERTIES = ["error", "message", "details", "request_id"]
ERROR_REQUIRED_REQUIRED = ["error", "message", "request_id"]


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc


def validate_schema_is_object(name: str, data: dict) -> None:
    if data.get("type") != "object":
        raise ValueError(f"{name}: schema type must be object")


def validate_precision_contract(data: dict) -> None:
    validate_schema_is_object("precision_contract", data)
    props = data.get("properties", {})
    missing_props = [p for p in REQUIRED_PROPERTIES if p not in props]
    if missing_props:
        raise ValueError(f"precision_contract: missing properties: {', '.join(missing_props)}")

    required = data.get("required", [])
    missing_required = [p for p in REQUIRED_REQUIRED if p not in required]
    if missing_required:
        raise ValueError(f"precision_contract: required[] missing: {', '.join(missing_required)}")

    # Lightweight structural checks (not a JSON Schema validator).
    conf = props.get("confidence", {})
    if conf.get("type") != "number":
        raise ValueError("precision_contract: confidence.type must be number")
    if "minimum" not in conf or "maximum" not in conf:
        raise ValueError("precision_contract: confidence must define minimum and maximum")
    if conf.get("minimum") != 0.0 or conf.get("maximum") != 1.0:
        raise ValueError("precision_contract: confidence minimum/maximum must be 0.0/1.0")

    candidates = props.get("candidates", {})
    if candidates.get("type") != "array":
        raise ValueError("precision_contract: candidates.type must be array")

    method = props.get("method", {})
    if method.get("type") != "string":
        raise ValueError("precision_contract: method.type must be string")

    limits = props.get("limits", {})
    if limits.get("type") != "string":
        raise ValueError("precision_contract: limits.type must be string")


def validate_error_response(data: dict) -> None:
    validate_schema_is_object("error_response", data)
    if data.get("additionalProperties") is not False:
        raise ValueError("error_response: additionalProperties must be false")

    props = data.get("properties", {})
    missing_props = [p for p in ERROR_REQUIRED_PROPERTIES if p not in props]
    if missing_props:
        raise ValueError(f"error_response: missing properties: {', '.join(missing_props)}")

    required = data.get("required", [])
    missing_required = [p for p in ERROR_REQUIRED_REQUIRED if p not in required]
    if missing_required:
        raise ValueError(f"error_response: required[] missing: {', '.join(missing_required)}")

    # Lightweight structural checks (not a JSON Schema validator).
    err = props.get("error", {})
    if err.get("type") != "string":
        raise ValueError("error_response: error.type must be string")
    if err.get("pattern") != "^[A-Z0-9_]+$":
        raise ValueError("error_response: error.pattern must be ^[A-Z0-9_]+$")

    details = props.get("details", {})
    if details.get("type") != "object":
        raise ValueError("error_response: details.type must be object")

    request_id = props.get("request_id", {})
    if request_id:
        if request_id.get("type") != "string":
            raise ValueError("error_response: request_id.type must be string")
        if request_id.get("format") != "uuid":
            raise ValueError("error_response: request_id.format must be uuid")


def main() -> int:
    for path in (PRECISION_SCHEMA, ERROR_SCHEMA):
        if not path.exists():
            print(f"ERROR: {path} not found")
            return 1

    try:
        precision = load_json(PRECISION_SCHEMA)
        validate_precision_contract(precision)

        err = load_json(ERROR_SCHEMA)
        validate_error_response(err)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    print("OK: contracts validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
