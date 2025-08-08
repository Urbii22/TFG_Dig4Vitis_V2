from __future__ import annotations

import numpy as np


def compute_coverage_percentage(common_leaf_mask: np.ndarray, final_drops_mask: np.ndarray) -> float:
    """Calcula el porcentaje de recubrimiento sobre la hoja común.

    Devuelve un valor en porcentaje (0.0–100.0).
    """
    total_leaf_pixels = int(np.count_nonzero(common_leaf_mask))
    if total_leaf_pixels == 0:
        return 0.0
    total_drop_pixels = int(np.count_nonzero(final_drops_mask))
    return (total_drop_pixels / total_leaf_pixels) * 100.0


