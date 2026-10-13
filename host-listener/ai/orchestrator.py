import copy
from typing import Any
from ai.schemas import VALID_COORDS
from ai.llm_engine import extract_constraints_with_ollama
from ai.ml_optimizer import SimulatedAnnealingOptimizer
from utils.logger import get_logger

logger = get_logger("AIOrchestrator")


def _detect_relevant_layers(
    prompt: str,
    layers: list[dict[str, Any]],
    target_layer_id: int | None
) -> list[int]:
    """
    Determines which editable layers (1, 2, 3) to optimize.
    Layer 0 (FN Keys F13-F24) is always excluded.
    """
    if target_layer_id in (1, 2, 3):
        return [target_layer_id]

    prompt_lower = prompt.lower()
    matched_layers: list[int] = []

    for layer in layers:
        lid = layer.get("id")
        if lid not in (1, 2, 3):
            continue
        keys = layer.get("keys", {})
        for key_obj in keys.values():
            lbl = str(key_obj.get("label", "")).strip().lower()
            if lbl and len(lbl) >= 3 and lbl in prompt_lower:
                if lid not in matched_layers:
                    matched_layers.append(lid)

    return matched_layers if matched_layers else [1, 2, 3]


def optimize_layout(
    prompt: str,
    current_config: dict[str, Any],
    telemetry: dict[str, Any],
    target_layer_id: int | None = None,
    model_name: str = "llama3.2"
) -> dict[str, Any]:
    """
    Executes the hybrid Ollama (LLM) -> Simulated Annealing (ML) optimization pipeline.
    Returns the proposed configuration and human-readable change summary.
    """
    if not prompt:
        return {"ok": False, "error": "Please enter a layout prompt."}

    if not isinstance(current_config, dict) or "layers" not in current_config:
        return {"ok": False, "error": "Invalid active configuration structure."}

    proposed_config = copy.deepcopy(current_config)
    layers = proposed_config.get("layers", [])

    layers_to_process = _detect_relevant_layers(prompt, layers, target_layer_id)
    explanations: list[str] = []
    moved_items: list[str] = []
    all_constraints: dict[int, Any] = {}

    for layer in layers:
        lid = layer.get("id")
        if lid == 0 or lid not in layers_to_process:
            continue

        layer_name = str(layer.get("name", f"Layer {lid + 1}"))
        original_keys: dict[str, dict[str, Any]] = layer.get("keys", {})

        # Build stripped coordinate -> label dictionary for the LLM
        coord_to_label: dict[str, str] = {}
        for coord in VALID_COORDS:
            k_obj = original_keys.get(coord)
            if k_obj and k_obj.get("label"):
                coord_to_label[coord] = str(k_obj["label"])

        if not coord_to_label:
            continue

        # 1. Qualitative Step: Extract semantic constraints via local Ollama
        constraints = extract_constraints_with_ollama(
            user_prompt=prompt,
            layer_id=lid,
            layer_name=layer_name,
            coord_to_label=coord_to_label,
            model_name=model_name
        )
        all_constraints[lid] = constraints
        if constraints.get("explanation"):
            explanations.append(f"[{layer_name}] {constraints['explanation']}")

        # 2. Quantitative Step: Run Simulated Annealing spatial solver
        solver = SimulatedAnnealingOptimizer(
            layer_id=lid,
            original_keys=original_keys,
            constraints=constraints,
            telemetry=telemetry,
            all_layers_config=layers
        )
        optimized_keys = solver.solve()
        layer["keys"] = optimized_keys

        # 3. Record coordinate changes for the summary
        for new_coord, new_obj in optimized_keys.items():
            lbl = new_obj.get("label")
            orig_coord = solver.original_label_coord.get(lbl)
            if lbl and orig_coord and orig_coord != new_coord:
                moved_items.append(f"{lbl} ({orig_coord} → {new_coord})")

    if moved_items:
        summary = f"Moved {len(moved_items)} key(s): " + ", ".join(moved_items[:5])
        if len(moved_items) > 5:
            summary += f" (+{len(moved_items) - 5} more)"
    else:
        summary = "Layout already satisfies constraints and telemetry; no key swaps needed."

    full_explanation = "\n".join(explanations)
    if moved_items:
        full_explanation += "\n\nRelocated: " + ", ".join(moved_items)

    return {
        "ok": True,
        "proposed_config": proposed_config,
        "summary": summary,
        "explanation": full_explanation.strip(),
        "constraints": all_constraints
    }
