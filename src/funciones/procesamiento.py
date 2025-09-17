import time
from collections.abc import Sequence

import cv2
import numpy as np
from skimage.morphology import (
    remove_small_holes,
    remove_small_objects,
)

from .alignment import _remove_petiole, compute_affine_transform


# -------------------------------------------------------------------
# Máscaras básicas
# -------------------------------------------------------------------
def _obtener_mascaras(
    imagen,
    *,
    banda_hoja: int | None = None,
    umbral_hoja: float | None = None,
    banda_producto: int | None = None,
    rangos_producto: Sequence[tuple[float, float]] | None = None,
    factor: float = 10000.0,
):
    """
    Calcula dos máscaras binarias a partir del cubo hiperespectral.

    Args:
        imagen: Cubo hiperespectral con forma (alto, ancho, bandas).
        banda_hoja: Número de banda (1-indexado) para segmentar la hoja.
        umbral_hoja: Umbral aplicado sobre la banda de la hoja.
        banda_producto: Número de banda (1-indexado) para detectar producto.
        rangos_producto: Secuencia de pares (mín, máx) sobre la intensidad escalada.
        factor: Escala aplicada a las reflectancias antes de comparar.
    """
    if len(imagen.shape) < 3:
        raise ValueError("La imagen debe contener una dimensión espectral.")

    _, _, total_bandas = imagen.shape
    if total_bandas <= 0:
        raise ValueError("La imagen no contiene bandas espectrales.")

    banda_hoja = 10 if banda_hoja is None else int(banda_hoja)
    banda_producto = 165 if banda_producto is None else int(banda_producto)
    umbral_hoja_val = 2000.0 if umbral_hoja is None else float(umbral_hoja)

    hoja_idx = banda_hoja - 1
    producto_idx = banda_producto - 1

    if not 0 <= hoja_idx < total_bandas:
        raise ValueError(
            f"La banda seleccionada para la hoja ({banda_hoja}) está fuera del rango 1-{total_bandas}."
        )
    if not 0 <= producto_idx < total_bandas:
        raise ValueError(
            f"La banda seleccionada para el producto ({banda_producto}) está fuera del rango 1-{total_bandas}."
        )

    b_hoja = imagen[:, :, hoja_idx].squeeze() * factor
    b_producto = imagen[:, :, producto_idx].squeeze() * factor

    leaf = remove_small_holes(b_hoja < umbral_hoja_val, area_threshold=200)

    if rangos_producto is None:
        rangos = ((3900.0, 4300.0), (4900.0, 5200.0))
    else:
        rangos = []
        for minimo, maximo in rangos_producto:
            if minimo is None or maximo is None:
                continue
            low = float(min(minimo, maximo))
            high = float(max(minimo, maximo))
            rangos.append((low, high))
        rangos = tuple(rangos)

    drops = np.zeros_like(b_producto, dtype=bool)
    for low, high in rangos:
        drops |= (b_producto >= low) & (b_producto <= high)

    return leaf, drops


def _trinarizar(leaf, drops, color_drops=(255, 0, 0)):
    """Construye imagen trinarizada (R,G,B) a partir de las máscaras."""
    h, w = leaf.shape
    out = np.zeros((h, w, 3), dtype=np.uint8)
    out[leaf] = [0, 255, 0]
    out[drops] = list(color_drops)
    return out


def trinarizar_final(
    leaf_mask: np.ndarray,
    current_drops_mask: np.ndarray,
    aligned_drops_to_subtract_mask: np.ndarray,
    min_drop_size: int = 1,
) -> np.ndarray:
    """
    Genera una imagen trinarizada (hoja, gotas únicas).
    """
    effective_drops = current_drops_mask & leaf_mask
    unique_drops = effective_drops & ~aligned_drops_to_subtract_mask

    if min_drop_size > 0:
        cleaned_unique_drops = remove_small_objects(
            unique_drops.astype(bool), min_size=min_drop_size
        )
    else:
        cleaned_unique_drops = unique_drops

    return _trinarizar(leaf_mask, cleaned_unique_drops)


# -------------------------------------------------------------------
# Máscaras y RGB
# -------------------------------------------------------------------
def band_idx(im, wl: float) -> int:
    centers = np.array([float(x) for x in im.bands.centers])
    return int(np.abs(centers - wl).argmin())


def to_rgb(im, wl_r: float = 639.1, wl_g: float = 548.4, wl_b: float = 459.2) -> np.ndarray:
    b = cv2.normalize(im.read_band(band_idx(im, wl_b)), None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    g = cv2.normalize(im.read_band(band_idx(im, wl_g)), None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    r = cv2.normalize(im.read_band(band_idx(im, wl_r)), None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    img = cv2.merge([b, g, r]).astype(np.float32)
    B, G, R = cv2.split(img)
    mean_lum = (B.mean() + G.mean() + R.mean()) / 3
    for ch in (B, G, R):
        ch *= mean_lum / (ch.mean() + 1e-8)
    return np.clip(cv2.merge([B, G, R]), 0, 255).astype(np.uint8)


# -------------------------------------------------------------------
# Procesamientos principales
# -------------------------------------------------------------------
def aplicar_procesamiento_dual(
    img_con: np.ndarray,
    img_sin: np.ndarray,
    *,
    orb_nfeatures: int | None = None,
    detection_scale_factor: float | None = None,
    ransac_reproj_thresh: float | None = None,
    ransac_max_iters: int | None = None,
    ransac_confidence: float | None = None,
    leaf_band: int | None = None,
    leaf_threshold: float | None = None,
    product_band: int | None = None,
    product_ranges: Sequence[tuple[float, float]] | None = None,
    intensity_scale: float = 10000.0,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    tuple[int, int],
    np.ndarray,
    np.ndarray,
    dict,
]:
    """
    Flujo completo SIN/CON con alineación por ORB/RANSAC.
    """
    # 1) Máscaras crudas a tamaño original
    leaf_con, drops_con_raw = _obtener_mascaras(
        img_con,
        banda_hoja=leaf_band,
        umbral_hoja=leaf_threshold,
        banda_producto=product_band,
        rangos_producto=product_ranges,
        factor=intensity_scale,
    )
    leaf_sin, drops_sin_raw = _obtener_mascaras(
        img_sin,
        banda_hoja=leaf_band,
        umbral_hoja=leaf_threshold,
        banda_producto=product_band,
        rangos_producto=product_ranges,
        factor=intensity_scale,
    )

    # 2) Determinar un lienzo común (el más grande) y colocar las máscaras en él
    h_con, w_con = leaf_con.shape
    h_sin, w_sin = leaf_sin.shape
    max_h = max(h_con, h_sin)
    max_w = max(w_con, w_sin)

    ref_mask_on_canvas = np.zeros((max_h, max_w), dtype=np.uint8)
    ref_mask_on_canvas[:h_con, :w_con] = (leaf_con * 255).astype(np.uint8)

    to_align_mask_on_canvas = np.zeros((max_h, max_w), dtype=np.uint8)
    to_align_mask_on_canvas[:h_sin, :w_sin] = (leaf_sin * 255).astype(np.uint8)

    to_align_drops_on_canvas = np.zeros((max_h, max_w), dtype=np.uint8)
    to_align_drops_on_canvas[:h_sin, :w_sin] = (drops_sin_raw * 255).astype(np.uint8)

    # 3) Alineación por ORB/RANSAC sobre los lienzos del mismo tamaño
    warp_mat = np.eye(2, 3, dtype=np.float32)

    t0 = time.perf_counter()
    try:
        limbo_con = _remove_petiole(ref_mask_on_canvas)
        limbo_sin = _remove_petiole(to_align_mask_on_canvas)

        edges_con = cv2.Canny(limbo_con, 50, 150)
        edges_sin = cv2.Canny(limbo_sin, 50, 150)

        kwargs = {}
        if orb_nfeatures is not None:
            kwargs["nfeatures"] = int(orb_nfeatures)
        if detection_scale_factor is not None:
            kwargs["detection_scale_factor"] = float(detection_scale_factor)
        if ransac_reproj_thresh is not None:
            kwargs["reproj_thresh"] = float(ransac_reproj_thresh)
        if ransac_max_iters is not None:
            kwargs["max_iters"] = int(ransac_max_iters)
        if ransac_confidence is not None:
            kwargs["confidence"] = float(ransac_confidence)

        result = compute_affine_transform(edges_con, edges_sin, return_metrics=True, **kwargs)
        if isinstance(result, tuple):
            warp_mat, metrics = result
        else:
            warp_mat = result
            metrics = {}

    except (RuntimeError, cv2.error) as e:
        print(f"Fallo en la alineación: {e}. Se usará la matriz identidad.")
        metrics = {"error": str(e)}
    t1 = time.perf_counter()
    metrics["alignment_time_s"] = t1 - t0

    # 4) Aplicar Warp a las máscaras SIN sobre el lienzo grande para evitar cortes
    dsize = (max_w, max_h)

    leaf_sin_aligned = cv2.warpAffine(
        to_align_mask_on_canvas, warp_mat, dsize, flags=cv2.INTER_NEAREST
    ).astype(bool)

    drops_sin_aligned = cv2.warpAffine(
        to_align_drops_on_canvas, warp_mat, dsize, flags=cv2.INTER_NEAREST
    ).astype(bool)

    # 5) Hoja común y gotas restringidas
    leaf_con_final = ref_mask_on_canvas.astype(bool)
    hoja_comun = leaf_con_final & leaf_sin_aligned

    drops_con_on_canvas = np.zeros((max_h, max_w), dtype=bool)
    drops_con_on_canvas[:h_con, :w_con] = drops_con_raw

    gotas_con = drops_con_on_canvas & hoja_comun
    gotas_sin = drops_sin_aligned & hoja_comun

    gotas_final = gotas_con & ~gotas_sin

    # 6) Trinarizada final
    trinarizada_result = _trinarizar(hoja_comun, gotas_final)

    return (
        trinarizada_result,
        leaf_con_final,
        leaf_sin_aligned,
        (max_h, max_w),
        hoja_comun,
        gotas_final,
        metrics,
    )
