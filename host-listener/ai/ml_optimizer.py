import copy
import math
import random
from typing import Any
from ai.schemas import VALID_COORDS, coord_to_xy
from utils.logger import get_logger

logger = get_logger("MLOptimizer")


def euclidean_dist(c1: str, c2: str) -> float:
    x1, y1 = coord_to_xy(c1)
    x2, y2 = coord_to_xy(c2)
    return math.hypot(x1 - x2, y1 - y2)


class SimulatedAnnealingOptimizer:
    """
    Stochastic spatial solver for the 3x4 ApexPad matrix (C0R0 - C2R3).
    Swaps complete key objects atomically while minimizing constraint penalties
    and physical finger travel distance.
    """

    def __init__(
        self,
        layer_id: int,
        original_keys: dict[str, dict[str, Any]],
        constraints: dict[str, Any],
        telemetry: dict[str, Any],
        all_layers_config: list[dict[str, Any]]
    ) -> None:
        self.layer_id = layer_id
        self.original_keys = copy.deepcopy(original_keys)
        self.constraints = constraints
        self.telemetry = telemetry
        self.all_layers_config = all_layers_config

        # Map each key's unique label to its original coordinate
        self.original_label_coord: dict[str, str] = {}
        for coord in VALID_COORDS:
            key_obj = self.original_keys.get(coord)
            if key_obj and key_obj.get("label"):
                self.original_label_coord[key_obj["label"]] = coord

        # Convert coordinate-based telemetry into label-based telemetry so history
        # follows the macro when its coordinate changes
        self.label_counts: dict[str, int] = {}
        self.intra_label_transitions: dict[tuple[str, str], int] = {}
        self.z_axis_target_Bonus: dict[str, dict[str, int]] = {}
        self._build_telemetry_maps()

    def _build_telemetry_maps(self) -> None:
        layer_str = str(self.layer_id)
        coord_to_label = {
            c: self.original_keys[c]["label"]
            for c in VALID_COORDS
            if c in self.original_keys and self.original_keys[c].get("label")
        }

        # 1. Key press counts per label
        raw_counts = self.telemetry.get("key_counts", {}).get(layer_str, {})
        for coord, count in raw_counts.items():
            lbl = coord_to_label.get(coord)
            if lbl and isinstance(count, int):
                self.label_counts[lbl] = self.label_counts.get(lbl, 0) + count

        # 2. Intra-layer sequential transitions (Label A -> Label B)
        raw_intra = self.telemetry.get("intra_layer_transitions", {}).get(layer_str, {})
        for pair_str, count in raw_intra.items():
            if "->" not in pair_str or not isinstance(count, int):
                continue
            c_from, c_to = pair_str.split("->", 1)
            lbl_a = coord_to_label.get(c_from)
            lbl_b = coord_to_label.get(c_to)
            if lbl_a and lbl_b and lbl_a != lbl_b:
                pair_key = (lbl_a, lbl_b)
                self.intra_label_transitions[pair_key] = (
                    self.intra_label_transitions.get(pair_key, 0) + count
                )

        # 3. Cross-layer Z-axis transitions (aligning physical coordinate across EC11 switches)
        raw_cross = self.telemetry.get("cross_layer_transitions", {})
        prefix = f"L{self.layer_id}:"
        for cross_str, count in raw_cross.items():
            if "->" not in cross_str or not isinstance(count, int):
                continue
            left_part, right_part = cross_str.split("->", 1)
            if left_part.startswith(prefix):
                my_orig_coord = left_part.split(":", 1)[1]
                other_coord = right_part.split(":", 1)[1]
            elif right_part.startswith(prefix):
                my_orig_coord = right_part.split(":", 1)[1]
                other_coord = left_part.split(":", 1)[1]
            else:
                continue

            my_lbl = coord_to_label.get(my_orig_coord)
            if my_lbl and other_coord in VALID_COORDS:
                coord_map = self.z_axis_target_Bonus.setdefault(my_lbl, {})
                coord_map[other_coord] = coord_map.get(other_coord, 0) + count

    def _calculate_cost(self, state_grid: dict[str, dict[str, Any] | None]) -> float:
        cost = 0.0

        label_to_coord: dict[str, str] = {}
        for coord, obj in state_grid.items():
            if obj and obj.get("label"):
                label_to_coord[obj["label"]] = coord

        # 1. Hard Constraint: Anchors
        anchors: dict[str, str] = self.constraints.get("anchors", {})
        for lbl, target_coord in anchors.items():
            curr_coord = label_to_coord.get(lbl)
            if curr_coord and curr_coord != target_coord:
                cost += 10000.0 * (1.0 + euclidean_dist(curr_coord, target_coord))

        # 2. Hard Constraint: Separations (prevent adjacent placement of misclicked keys)
        separations: list[list[str]] = self.constraints.get("separations", [])
        for pair in separations:
            c1 = label_to_coord.get(pair[0])
            c2 = label_to_coord.get(pair[1])
            if c1 and c2:
                dist = euclidean_dist(c1, c2)
                if dist < 1.5:  # Orthogonally (1.0) or diagonally (1.414) adjacent
                    cost += 6000.0 / max(dist, 0.5)
                else:
                    # Reward placing separated keys further apart
                    cost -= 35.0 * dist

        # 3. Semantic Constraint: Clusters (keep related keys contiguous)
        clusters: list[list[str]] = self.constraints.get("clusters", [])
        for group in clusters:
            coords = [label_to_coord[lbl] for lbl in group if lbl in label_to_coord]
            if len(coords) >= 2:
                for i in range(len(coords)):
                    # Distance to nearest neighbor within the same cluster
                    min_dist = min(
                        euclidean_dist(coords[i], coords[j])
                        for j in range(len(coords))
                        if i != j
                    )
                    if min_dist > 1.05:
                        cost += 450.0 * (min_dist - 1.0)
                    else:
                        cost -= 40.0

        # 4. Quantitative Telemetry: Intra-Layer X/Y Transition Distance
        for (lbl_a, lbl_b), count in self.intra_label_transitions.items():
            c1 = label_to_coord.get(lbl_a)
            c2 = label_to_coord.get(lbl_b)
            if c1 and c2:
                cost += count * 25.0 * euclidean_dist(c1, c2)

        # 5. Quantitative Telemetry: High-Frequency Ergonomic Placement
        # Bottom and outer rows (R3, R2) require less reach over the keypad than the middle-top
        for lbl, count in self.label_counts.items():
            c = label_to_coord.get(lbl)
            if c:
                _, row = coord_to_xy(c)
                ergo_penalty = (3 - row) * 2.5
                cost += count * ergo_penalty

        # 6. Quantitative Telemetry: Z-Axis Cross-Layer Coordinate Alignment
        for lbl, target_coords in self.z_axis_target_Bonus.items():
            curr_c = label_to_coord.get(lbl)
            if curr_c:
                for target_c, count in target_coords.items():
                    cost += count * 18.0 * euclidean_dist(curr_c, target_c)

        # 7. Stability Bias: Keep uninvolved keys in their original coordinates
        for lbl, curr_c in label_to_coord.items():
            orig_c = self.original_label_coord.get(lbl)
            if orig_c and curr_c != orig_c:
                cost += 3.5 * euclidean_dist(curr_c, orig_c)

        return cost

    def solve(self, iterations: int = 3500) -> dict[str, dict[str, Any]]:
        # Initialize 12-slot state grid
        current_grid: dict[str, dict[str, Any] | None] = {
            c: copy.deepcopy(self.original_keys.get(c)) for c in VALID_COORDS
        }

        # Pre-satisfy explicit anchors by swapping anchored keys into place immediately
        anchors: dict[str, str] = self.constraints.get("anchors", {})
        locked_coords: set[str] = set()

        for lbl, target_coord in anchors.items():
            if target_coord not in VALID_COORDS:
                continue
            source_coord = None
            for c, obj in current_grid.items():
                if obj and obj.get("label") == lbl:
                    source_coord = c
                    break
            if source_coord:
                current_grid[source_coord], current_grid[target_coord] = (
                    current_grid[target_coord],
                    current_grid[source_coord]
                )
                locked_coords.add(target_coord)

        swappable_coords = [c for c in VALID_COORDS if c not in locked_coords]

        current_cost = self._calculate_cost(current_grid)
        best_grid = copy.deepcopy(current_grid)
        best_cost = current_cost

        if len(swappable_coords) >= 2:
            rng = random.Random(42)
            temp = 1200.0
            cooling_rate = 0.9975

            for _ in range(iterations):
                c1, c2 = rng.sample(swappable_coords, 2)
                current_grid[c1], current_grid[c2] = current_grid[c2], current_grid[c1]

                candidate_cost = self._calculate_cost(current_grid)
                delta = candidate_cost - current_cost

                if delta < 0 or rng.random() < math.exp(-delta / max(temp, 1e-6)):
                    current_cost = candidate_cost
                    if current_cost < best_cost:
                        best_cost = current_cost
                        best_grid = copy.deepcopy(current_grid)
                else:
                    # Revert swap
                    current_grid[c1], current_grid[c2] = current_grid[c2], current_grid[c1]

                temp *= cooling_rate

        # Rebuild clean dictionary excluding empty/None slots
        optimized_keys: dict[str, dict[str, Any]] = {}
        for coord in VALID_COORDS:
            if best_grid[coord] is not None:
                optimized_keys[coord] = best_grid[coord]  # type: ignore[assignment]

        return optimized_keys
