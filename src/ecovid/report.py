from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import cv2
import numpy as np


def build_zip_report(
    *,
    result_image_rgb: np.ndarray,
    final_drops_mask: np.ndarray,
    coverage_percent: float,
    metrics: dict | None = None,
    output_zip: str | Path = "reporte.zip",
) -> Path:
    """Empaqueta un ZIP autocontenido con imagen, máscara y metadatos reproducibles."""
    png_bytes = cv2.imencode(".png", cv2.cvtColor(result_image_rgb, cv2.COLOR_RGB2BGR))[1].tobytes()
    mask_bytes = cv2.imencode(".png", (final_drops_mask.astype(np.uint8) * 255))[1].tobytes()

    metadata = {
        "coverage_percent": coverage_percent,
        "metrics": metrics or {},
        "sha256_result_png": hashlib.sha256(png_bytes).hexdigest(),
    }
    meta_bytes = json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8")

    out = Path(output_zip)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr("resultado.png", png_bytes)
        zf.writestr("mask_gotas.png", mask_bytes)
        zf.writestr("metadata.json", meta_bytes)
    return out
