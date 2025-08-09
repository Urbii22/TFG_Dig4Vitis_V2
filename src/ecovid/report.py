from __future__ import annotations

import hashlib
import io
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
    """Empaqueta un ZIP autocontenido con imagen, máscara y metadatos reproducibles.

    Incluye también un reporte HTML simple para visualización rápida offline.
    """
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
        # Reporte HTML básico
        html = (
            "<!doctype html><meta charset='utf-8'>"
            "<h1>Reporte EcoVid</h1>"
            f"<p>Porcentaje de recubrimiento: {coverage_percent:.2f}%</p>"
            "<p>Imagen resultante:</p>"
            "<img src='resultado.png' style='max-width:100%;height:auto'>"
            "<p>Máscara de gotas:</p>"
            "<img src='mask_gotas.png' style='max-width:100%;height:auto'>"
        )
        zf.writestr("reporte.html", html.encode("utf-8"))
        # Reporte PDF (si reportlab está disponible)
        try:
            pdf_bytes = build_pdf_report(
                result_image_rgb=result_image_rgb,
                final_drops_mask=final_drops_mask,
                coverage_percent=coverage_percent,
                metrics=metrics or {},
            )
            zf.writestr("reporte.pdf", pdf_bytes)
        except Exception:
            # PDF opcional; si falla, omitimos sin romper el ZIP
            pass
    return out


def build_pdf_report(
    *,
    result_image_rgb: np.ndarray,
    final_drops_mask: np.ndarray,
    coverage_percent: float,
    metrics: dict | None = None,
) -> bytes:
    """Genera un PDF en memoria con resumen de resultados e imágenes."""
    from PIL import Image
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    width, height = A4  # puntos (1/72 inch)
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # Título
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 50, "Reporte EcoVid")

    # Métricas
    c.setFont("Helvetica", 11)
    y = height - 80
    c.drawString(40, y, f"Porcentaje de recubrimiento: {coverage_percent:.2f}%")
    y -= 16
    if metrics:
        for key in [
            "n_matches",
            "n_inliers",
            "inlier_ratio",
            "mean_reproj_error_px",
            "alignment_time_s",
        ]:
            if key in metrics:
                val = metrics[key]
                if key == "inlier_ratio":
                    val = f"{val*100:.1f}%"
                elif isinstance(val, float):
                    val = f"{val:.3f}"
                c.drawString(40, y, f"{key}: {val}")
                y -= 14

    # Imágenes (resultado y máscara)
    def pil_from_array(arr: np.ndarray) -> Image.Image:
        if arr.ndim == 2:
            return Image.fromarray(arr.astype(np.uint8) * 255)
        if arr.shape[2] == 3:
            return Image.fromarray(arr)
        raise ValueError("Formato de imagen no soportado")

    img_res = pil_from_array(result_image_rgb)
    img_msk = pil_from_array(final_drops_mask.astype(np.uint8))

    max_w = width - 80
    max_h = (height / 2) - 80

    def draw_image(pil_img: Image.Image, x: float, y: float):
        w, h = pil_img.size
        scale = min(max_w / w, max_h / h)
        new_size = (int(w * scale), int(h * scale))
        img_resized = pil_img.resize(new_size)
        c.drawImage(ImageReader(img_resized), x, y, width=new_size[0], height=new_size[1])

    # Posiciones
    left_x = 40
    right_x = width / 2 + 10
    bottom_y = height / 2 - 40

    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_x, bottom_y + max_h + 12, "Resultado (RGB)")
    draw_image(img_res, left_x, bottom_y)

    c.drawString(right_x, bottom_y + max_h + 12, "Máscara de gotas")
    draw_image(img_msk, right_x, bottom_y)

    c.showPage()
    c.save()
    return buffer.getvalue()
