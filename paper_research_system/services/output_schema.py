"""
Minimal output schema validation for tests.
"""
from typing import Dict, Any, List


class SchemaValidationError(Exception):
    pass


def validate_output_schema(data: Dict[str, Any]) -> None:
    """Validate that data matches the expected minimal schema.

    Expected shape: { "claims": [ { "text": str, "verdict": str, "evidence": list } ] }
    Verdict must be one of: confirmed | contested | unknown
    """
    if not isinstance(data, dict):
        raise SchemaValidationError("payload must be a dict")

    claims = data.get("claims")
    if claims is None or not isinstance(claims, list):
        raise SchemaValidationError("claims must be a list")

    allowed_verdicts = {"confirmed", "contested", "unknown"}

    for idx, c in enumerate(claims):
        if not isinstance(c, dict):
            raise SchemaValidationError(f"claim[{idx}] must be an object")
        text = c.get("text")
        verdict = c.get("verdict")
        evidence = c.get("evidence", [])

        if not isinstance(text, str):
            raise SchemaValidationError(f"claim[{idx}].text must be a string")
        if verdict not in allowed_verdicts:
            raise SchemaValidationError(
                f"claim[{idx}].verdict must be one of {sorted(allowed_verdicts)}"
            )
        if not isinstance(evidence, list):
            raise SchemaValidationError(f"claim[{idx}].evidence must be a list")

    # If all checks pass, return None
    return None


