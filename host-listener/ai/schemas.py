from typing import Any

VALID_COORDS: list[str] = [
    "C0R0", "C1R0", "C2R0",
    "C0R1", "C1R1", "C2R1",
    "C0R2", "C1R2", "C2R2",
    "C0R3", "C1R3", "C2R3"
]

COORD_ALIASES: dict[str, str] = {
    "TOP-LEFT": "C0R0",
    "TOP LEFT": "C0R0",
    "UPPER-LEFT": "C0R0",
    "TOP-CENTER": "C1R0",
    "TOP CENTER": "C1R0",
    "TOP-MIDDLE": "C1R0",
    "TOP-RIGHT": "C2R0",
    "TOP RIGHT": "C2R0",
    "UPPER-RIGHT": "C2R0",
    "BOTTOM-LEFT": "C0R3",
    "BOTTOM LEFT": "C0R3",
    "LOWER-LEFT": "C0R3",
    "BOTTOM-CENTER": "C1R3",
    "BOTTOM CENTER": "C1R3",
    "BOTTOM-MIDDLE": "C1R3",
    "BOTTOM-RIGHT": "C2R3",
    "BOTTOM RIGHT": "C2R3",
    "LOWER-RIGHT": "C2R3"
}

# JSON Schema enforced directly by Ollama's structured output engine
OLLAMA_CONSTRAINT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "anchors": {
            "type": "object",
            "description": "Map of exact key label to target coordinate (C0R0 to C2R3).",
            "additionalProperties": {
                "type": "string"
            }
        },
        "separations": {
            "type": "array",
            "description": "List of key label pairs that must be placed far apart to prevent misclicks.",
            "items": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "maxItems": 2
            }
        },
        "clusters": {
            "type": "array",
            "description": "List of key label groups that belong next to each other on the grid.",
            "items": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2
            }
        },
        "explanation": {
            "type": "string",
            "description": "Brief 1-2 sentence explanation of the spatial rules applied."
        }
    },
    "required": ["anchors", "separations", "clusters", "explanation"]
}


def coord_to_xy(coord: str) -> tuple[int, int]:
    """Converts 'C1R2' to (col=1, row=2)."""
    if len(coord) == 4 and coord[0] == "C" and coord[2] == "R":
        return int(coord[1]), int(coord[3])
    return 0, 0


def normalize_coord(raw_coord: str) -> str | None:
    """Normalizes a coordinate string or natural language corner alias into C0R0-C2R3."""
    if not raw_coord:
        return None
    cleaned = raw_coord.strip().upper()
    if cleaned in VALID_COORDS:
        return cleaned
    if cleaned in COORD_ALIASES:
        return COORD_ALIASES[cleaned]
    return None


def match_label(candidate: str, valid_labels: list[str]) -> str | None:
    """Case-insensitive and substring fuzzy matcher against actual layer labels."""
    if not candidate:
        return None
    cand_clean = candidate.strip().lower()
    for lbl in valid_labels:
        if lbl.lower() == cand_clean:
            return lbl
    for lbl in valid_labels:
        if cand_clean in lbl.lower() or lbl.lower() in cand_clean:
            return lbl
    return None


def validate_and_normalize_constraints(
    raw_rules: dict[str, Any],
    valid_labels: list[str]
) -> dict[str, Any]:
    """Sanitizes LLM output so only real key labels and valid C0R0-C2R3 coordinates pass through."""
    normalized_anchors: dict[str, str] = {}
    used_coords: set[str] = set()

    raw_anchors = raw_rules.get("anchors", {})
    if isinstance(raw_anchors, dict):
        for k, v in raw_anchors.items():
            if not isinstance(k, str) or not isinstance(v, str):
                continue
            # Handle case where LLM reverses {coord: label} instead of {label: coord}
            matched_lbl = match_label(k, valid_labels)
            norm_c = normalize_coord(v)
            if not matched_lbl or not norm_c:
                matched_lbl = match_label(v, valid_labels)
                norm_c = normalize_coord(k)

            if matched_lbl and norm_c and norm_c not in used_coords:
                normalized_anchors[matched_lbl] = norm_c
                used_coords.add(norm_c)

    normalized_separations: list[list[str]] = []
    raw_seps = raw_rules.get("separations", [])
    if isinstance(raw_seps, list):
        for pair in raw_seps:
            if isinstance(pair, list) and len(pair) >= 2:
                lbl_a = match_label(str(pair[0]), valid_labels)
                lbl_b = match_label(str(pair[1]), valid_labels)
                if lbl_a and lbl_b and lbl_a != lbl_b:
                    sorted_pair = sorted([lbl_a, lbl_b])
                    if sorted_pair not in normalized_separations:
                        normalized_separations.append(sorted_pair)

    normalized_clusters: list[list[str]] = []
    raw_clusters = raw_rules.get("clusters", [])
    if isinstance(raw_clusters, list):
        for group in raw_clusters:
            if isinstance(group, list) and len(group) >= 2:
                matched_group: list[str] = []
                for item in group:
                    m = match_label(str(item), valid_labels)
                    if m and m not in matched_group:
                        matched_group.append(m)
                if len(matched_group) >= 2:
                    normalized_clusters.append(matched_group)

    explanation = str(raw_rules.get("explanation", "")).strip()
    if not explanation:
        explanation = "Applied ergonomic constraints based on your feedback and usage telemetry."

    return {
        "anchors": normalized_anchors,
        "separations": normalized_separations,
        "clusters": normalized_clusters,
        "explanation": explanation
    }
