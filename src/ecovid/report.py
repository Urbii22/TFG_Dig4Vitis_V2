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
    # Opcionales para reporte enriquecido
    rgb_sin: np.ndarray | None = None,
    rgb_con: np.ndarray | None = None,
    trin_sin: np.ndarray | None = None,
    trin_con: np.ndarray | None = None,
    overlay_alignment: np.ndarray | None = None,
    stats: dict | None = None,
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
        # Imágenes opcionales
        if rgb_sin is not None:
            zf.writestr(
                "rgb_sin.png",
                cv2.imencode(".png", cv2.cvtColor(rgb_sin, cv2.COLOR_RGB2BGR))[1].tobytes(),
            )
        if rgb_con is not None:
            zf.writestr(
                "rgb_con.png",
                cv2.imencode(".png", cv2.cvtColor(rgb_con, cv2.COLOR_RGB2BGR))[1].tobytes(),
            )
        if trin_sin is not None:
            zf.writestr(
                "trin_sin.png",
                cv2.imencode(".png", cv2.cvtColor(trin_sin, cv2.COLOR_RGB2BGR))[1].tobytes(),
            )
        if trin_con is not None:
            zf.writestr(
                "trin_con.png",
                cv2.imencode(".png", cv2.cvtColor(trin_con, cv2.COLOR_RGB2BGR))[1].tobytes(),
            )
        if overlay_alignment is not None:
            zf.writestr(
                "overlay_alignment.png",
                cv2.imencode(".png", cv2.cvtColor(overlay_alignment, cv2.COLOR_RGB2BGR))[
                    1
                ].tobytes(),
            )

        # Metadata ampliada
        enriched_meta = {
            **json.loads(meta_bytes.decode("utf-8")),
            "sha256_mask_png": hashlib.sha256(mask_bytes).hexdigest(),
            "stats": stats or {},
        }
        zf.writestr(
            "metadata.json",
            json.dumps(enriched_meta, ensure_ascii=False, indent=2).encode("utf-8"),
        )
        # Reporte HTML básico
        html_parts = [
            "<!doctype html><meta charset='utf-8'>",
            "<style>body{font-family:system-ui,Segoe UI,Arial;margin:16px} .grid{display:grid;grid-template-columns:1fr 1fr;gap:12px} img{max-width:100%;height:auto;border:1px solid #ddd;border-radius:6px} table{border-collapse:collapse} td,th{border:1px solid #ddd;padding:6px}</style>",
            "<h1>Reporte EcoVid</h1>",
            f"<p><b>Porcentaje de recubrimiento:</b> {coverage_percent:.2f}%</p>",
        ]
        if stats:
            html_parts.append("<h3>Métricas</h3>")
            rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in stats.items())
            html_parts.append(f"<table><tbody>{rows}</tbody></table>")
        html_parts.append("<h3>Imágenes</h3>")
        html_parts.append("<div class='grid'>")
        html_parts.append("<div><h4>Resultado</h4><img src='resultado.png'></div>")
        html_parts.append("<div><h4>Máscara de gotas</h4><img src='mask_gotas.png'></div>")
        if rgb_sin is not None:
            html_parts.append("<div><h4>RGB SIN</h4><img src='rgb_sin.png'></div>")
        if rgb_con is not None:
            html_parts.append("<div><h4>RGB CON</h4><img src='rgb_con.png'></div>")
        if trin_sin is not None:
            html_parts.append("<div><h4>Trinarizada SIN</h4><img src='trin_sin.png'></div>")
        if trin_con is not None:
            html_parts.append("<div><h4>Trinarizada CON</h4><img src='trin_con.png'></div>")
        if overlay_alignment is not None:
            html_parts.append(
                "<div><h4>Overlay Alineación</h4><img src='overlay_alignment.png'></div>"
            )
        html_parts.append("</div>")
        html = "".join(html_parts)
        zf.writestr("reporte.html", html.encode("utf-8"))
        # Reporte PDF (si reportlab está disponible)
        try:
            pdf_bytes = build_pdf_report(
                result_image_rgb=result_image_rgb,
                final_drops_mask=final_drops_mask,
                coverage_percent=coverage_percent,
                metrics=metrics or {},
                rgb_sin=rgb_sin,
                rgb_con=rgb_con,
                trin_sin=trin_sin,
                trin_con=trin_con,
                overlay_alignment=overlay_alignment,
                stats=stats or {},
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
    rgb_sin: np.ndarray | None = None,
    rgb_con: np.ndarray | None = None,
    trin_sin: np.ndarray | None = None,
    trin_con: np.ndarray | None = None,
    overlay_alignment: np.ndarray | None = None,
    stats: dict | None = None,
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

    # Imágenes (resultado, máscara y opcionales)
    def pil_from_array(arr: np.ndarray) -> Image.Image:
        if arr.ndim == 2:
            return Image.fromarray(arr.astype(np.uint8) * 255)
        if arr.shape[2] == 3:
            return Image.fromarray(arr)
        raise ValueError("Formato de imagen no soportado")

    img_res = pil_from_array(result_image_rgb)
    img_msk = pil_from_array(final_drops_mask.astype(np.uint8))
    img_rgb_sin = pil_from_array(rgb_sin) if rgb_sin is not None else None
    img_rgb_con = pil_from_array(rgb_con) if rgb_con is not None else None
    img_trin_sin = pil_from_array(trin_sin) if trin_sin is not None else None
    img_trin_con = pil_from_array(trin_con) if trin_con is not None else None
    img_overlay = pil_from_array(overlay_alignment) if overlay_alignment is not None else None

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

    # Página 2: imágenes adicionales si existen
    y2 = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y2, "Imágenes adicionales")
    y2 -= 24

    slots = [
        ("RGB SIN", img_rgb_sin),
        ("RGB CON", img_rgb_con),
        ("Trinarizada SIN", img_trin_sin),
        ("Trinarizada CON", img_trin_con),
        ("Overlay Alineación", img_overlay),
    ]

    x = 40
    y = y2 - max_h - 12
    col = 0
    for title, img in slots:
        if img is None:
            continue
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y + max_h + 8, title)
        draw_image(img, x, y)
        col += 1
        if col % 2 == 1:
            x = width / 2 + 10
        else:
            x = 40
            y -= max_h + 40

    c.showPage()
    c.save()
    return buffer.getvalue()
