from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from spectral.io import envi


@dataclass
class DemoPaths:
    sin_hdr: Path
    sin_bil: Path
    con_hdr: Path
    con_bil: Path


def _generate_cube(
    height: int,
    width: int,
    bands: int,
    seed: int = 42,
    leaf_rect: tuple[int, int, int, int] = (20, 20, 140, 180),
    drops_rects: list[tuple[int, int, int, int]] | None = None,
    with_drops: bool = False,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    cube = rng.normal(loc=0.0, scale=1.0, size=(height, width, bands)).astype(np.float32)

    # Simular respuesta espectral suave por banda (gradiente)
    wl_profile = np.linspace(0.8, 1.2, bands, dtype=np.float32)
    cube *= wl_profile[None, None, :]

    # Definir hoja (rectángulo) con b10 bajo
    y0, x0, y1, x1 = leaf_rect
    cube[y0:y1, x0:x1, 9] = 0.15  # debajo de 0.2 (tras factor*10000 -> <2000)

    if with_drops:
        if not drops_rects:
            drops_rects = [(60, 60, 90, 100), (100, 120, 130, 150)]
        # Poner b164 dentro de rangos definidos en procesamiento.py
        for yy0, xx0, yy1, xx1 in drops_rects:
            cube[yy0:yy1, xx0:xx1, 164] = 0.45  # luego *10000 -> 4500 (en rango)

    return cube


def write_envi_pair(
    outdir: str | Path,
    *,
    height: int = 200,
    width: int = 220,
    bands: int = 180,
    seed: int = 42,
) -> DemoPaths:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    sin_cube = _generate_cube(height, width, bands, seed=seed, with_drops=False)
    con_cube = _generate_cube(height, width, bands, seed=seed, with_drops=True)

    sin_hdr = out / "demo_sin.hdr"
    con_hdr = out / "demo_con.hdr"

    # Guardar en formato ENVI con bil interleave
    envi.save_image(str(sin_hdr), sin_cube, interleave="bil", force=True)
    envi.save_image(str(con_hdr), con_cube, interleave="bil", force=True)

    return DemoPaths(
        sin_hdr=sin_hdr,
        sin_bil=sin_hdr.with_suffix(".bil"),
        con_hdr=con_hdr,
        con_bil=con_hdr.with_suffix(".bil"),
    )
