from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from spectral.io import envi

from funciones.procesamiento import aplicar_procesamiento_dual

from .metrics import compute_coverage_percentage


@dataclass
class ProcessResult:
    result_image_rgb: np.ndarray
    common_leaf_mask: np.ndarray
    final_drops_mask: np.ndarray
    coverage_percent: float


def load_envi_dataset(hdr_path: str | Path, bil_path: str | Path):
    """Abre un dataset ENVI desde rutas .hdr y .bil."""
    return envi.open(str(hdr_path), str(bil_path))


def process_pair(
    hdr_without: str | Path,
    bil_without: str | Path,
    hdr_with: str | Path,
    bil_with: str | Path,
) -> ProcessResult:
    """Procesa un par SIN/CON y devuelve imagen anotada y métricas básicas."""
    ds_without = load_envi_dataset(hdr_without, bil_without)
    ds_with = load_envi_dataset(hdr_with, bil_with)

    result_rgb, _leaf_con, _leaf_sin_aligned, _shape, common_leaf, final_drops = (
        aplicar_procesamiento_dual(ds_with, ds_without)
    )

    coverage = compute_coverage_percentage(common_leaf, final_drops)

    return ProcessResult(
        result_image_rgb=result_rgb,
        common_leaf_mask=common_leaf,
        final_drops_mask=final_drops,
        coverage_percent=coverage,
    )


def _ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def export_outputs(
    res: ProcessResult, output_dir: str | Path, stem: str = "resultado"
) -> tuple[Path, Path, Path]:
    """Exporta PNG anotado, máscara binaria y CSV de cobertura.

    Devuelve las rutas (png_anotado, mascara_png, csv).
    """
    out_dir = _ensure_dir(output_dir)

    # Imagen resultante (RGB) ya codificada por el pipeline (verde: hoja, rojo: gotas)
    png_path = out_dir / f"{stem}.png"
    bgr = cv2.cvtColor(res.result_image_rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(png_path), bgr)

    # Máscara binaria de gotas
    mask_path = out_dir / f"{stem}_mask_gotas.png"
    mask_u8 = res.final_drops_mask.astype(np.uint8) * 255
    cv2.imwrite(str(mask_path), mask_u8)

    # CSV de cobertura
    csv_path = out_dir / f"{stem}_cobertura.csv"
    csv_content = f"metrica,valor\nporcentaje_cobertura,{res.coverage_percent:.4f}\n"
    csv_path.write_text(csv_content, encoding="utf-8")

    return png_path, mask_path, csv_path
