"""
Error enrichment module.

Converts raw Python traceback or RPC error messages from FreeCAD
into descriptive, LLM-friendly messages.
"""

import re

# Known error patterns -> human-friendly explanations
_ERROR_PATTERNS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(r"Sketcher::ConstraintError.*edge\s+(\d+)", re.IGNORECASE),
        lambda m: (
            f"Conflicting constraints on edge #{m.group(1)}. "
            "Check current constraints with 'get_object_info' "
            "or remove the conflicting constraint."
        ),
    ),
    (
        re.compile(r"No document named '(.+)'", re.IGNORECASE),
        lambda m: (
            f"No document named '{m.group(1)}' found. "
            "List available documents using the 'list_documents' tool."
        ),
    ),
    (
        re.compile(r"Object '(.+)' not found", re.IGNORECASE),
        lambda m: (
            f"No object named '{m.group(1)}' found. "
            "Look at the objects in your document using 'get_object_tree'."
        ),
    ),
    (
        re.compile(r"Boolean operation failed", re.IGNORECASE),
        lambda _: (
            "Boolean operation failed. "
            "Check if the two objects are actually intersecting; "
            "overlapping the objects slightly might solve the issue."
        ),
    ),
    (
        re.compile(r"FreeCAD RPC sunucusuna bağlanılamadı|Could not connect to FreeCAD RPC server", re.IGNORECASE),
        lambda _: (
            "Could not connect to FreeCAD. Ensure FreeCAD is open and "
            "'freecad_rpc_server.py' is running. "
            "Start the server from the Macro menu."
        ),
    ),
    (
        re.compile(r"ConnectionRefusedError", re.IGNORECASE),
        lambda _: (
            "FreeCAD RPC connection refused. "
            "Ensure FreeCAD is open and the RPC server is listening on port 36875."
        ),
    ),
    (
        re.compile(r"Part::NullShapeException", re.IGNORECASE),
        lambda _: (
            "Invalid (null) geometry encountered. "
            "Check that dimensions are greater than zero and the sketch is properly closed."
        ),
    ),
    (
        re.compile(r"Pad.*failed|Pocket.*failed", re.IGNORECASE),
        lambda _: (
            "Pad/Pocket operation failed. "
            "Ensure all geometries in the sketch form a closed profile and "
            "the extrusion direction is correct."
        ),
    ),
]


def enrich_error(raw_message: str) -> str:
    """Converts a raw error message into an LLM-friendly message."""
    for pattern, builder in _ERROR_PATTERNS:
        m = pattern.search(raw_message)
        if m:
            return builder(m) if callable(builder) else builder
    # If no pattern matches, return the original message slightly formatted
    return f"FreeCAD error: {raw_message.strip()}"
