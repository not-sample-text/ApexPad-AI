import json
import urllib.request
import urllib.error
from typing import Any
from ai.schemas import OLLAMA_CONSTRAINT_SCHEMA, validate_and_normalize_constraints
from utils.logger import get_logger

logger = get_logger("LLMEngine")

OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"


def extract_constraints_with_ollama(
    user_prompt: str,
    layer_id: int,
    layer_name: str,
    coord_to_label: dict[str, str],
    model_name: str = "llama3.2"
) -> dict[str, Any]:
    """
    Sends the current layer's coordinate-to-label map and user feedback to local Ollama.
    Returns validated spatial constraints (anchors, separations, clusters, explanation).
    """
    valid_labels = [lbl for lbl in coord_to_label.values() if lbl]

    system_prompt = (
        "You are an ergonomic 3x4 macropad layout architect.\n"
        "The macropad has 3 columns (C0=left, C1=middle, C2=right) and 4 rows (R0=top, R1=upper-mid, R2=lower-mid, R3=bottom).\n"
        "Coordinate reference:\n"
        "- Top row (closest to OLED screen & rotary knob): C0R0 (top-left), C1R0 (top-center), C2R0 (top-right)\n"
        "- Second row: C0R1, C1R1, C2R1\n"
        "- Third row: C0R2, C1R2, C2R2\n"
        "- Bottom row (closest to user): C0R3 (bottom-left), C1R3 (bottom-center), C2R3 (bottom-right)\n\n"
        f"Active Layer: Layer {layer_id + 1} ({layer_name})\n"
        f"Current Key Coordinates & Labels: {json.dumps(coord_to_label)}\n\n"
        "Rules:\n"
        "1. Use ONLY exact key labels from the list above.\n"
        "2. 'anchors': Map a key label to a specific coordinate (C0R0-C2R3) if the user asks to pin/move a key to a specific spot, row, column, or corner.\n"
        "3. 'separations': Add pairs of key labels [LabelA, LabelB] if the user complains about misclicking one when reaching for the other, or wants dangerous/conflicting keys separated.\n"
        "4. 'clusters': Group related key labels [LabelA, LabelB, ...] that should be placed adjacent to each other (e.g., media/streaming tools, browsers/social, photo editing, games, or system cleanup).\n"
        "5. Provide a concise 'explanation' of the rules you set."
    )

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "format": OLLAMA_CONSTRAINT_SCHEMA,
        "stream": False,
        "options": {
            "temperature": 0.0
        }
    }

    req = urllib.request.Request(
        OLLAMA_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        logger.info(f"Querying local Ollama model '{model_name}' for Layer {layer_id}...")
        with urllib.request.urlopen(req, timeout=30) as response:
            resp_data = json.loads(response.read().decode("utf-8"))
            raw_content = resp_data.get("message", {}).get("content", "{}")
            parsed_json = json.loads(raw_content)
            validated = validate_and_normalize_constraints(parsed_json, valid_labels)
            logger.info(f"Extracted constraints for Layer {layer_id}: {validated}")
            return validated

    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        logger.error(f"Ollama HTTP Error {e.code}: {err_body}")
        raise RuntimeError(
            f"Ollama returned HTTP {e.code}. Ensure model '{model_name}' is installed ('ollama pull {model_name}')."
        ) from e
    except urllib.error.URLError as e:
        logger.error(f"Failed to connect to local Ollama instance: {e}")
        raise RuntimeError(
            "Could not connect to local Ollama at http://127.0.0.1:11434. "
            f"Please ensure Ollama is running and '{model_name}' is pulled."
        ) from e
    except Exception as e:
        logger.error(f"Error parsing Ollama response: {e}")
        raise RuntimeError(f"Failed to process LLM constraints: {e}") from e
