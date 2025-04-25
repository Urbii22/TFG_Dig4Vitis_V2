"""
Rutinas de backend para el procesado de imágenes hiperespectrales:
obtención de máscaras, alineación, trinarizados, etc.

No contiene ninguna dependencia de Streamlit ni código de interfaz.
"""

import math
import cv2
import numpy as np
from spectral.io import envi            # puede usarse desde otros módulos
from skimage.morphology import (
    remove_small_holes,
    remove_small_objects,
)

# -------------------------------------------------------------------
# Máscaras básicas
# -------------------------------------------------------------------
def _obtener_mascaras(imagen):
    """
    Calcula dos máscaras binarias a partir del cubo hiperespectral:

    Returns
    -------
    leaf_mask : np.ndarray[bool]
        Máscara de la hoja (región verde).
    drops_mask : np.ndarray[bool]
        Máscara de gotas sin limitar a la hoja.
    """
    factor = 10000
    b10  = imagen[:, :, 9].squeeze()   * factor
    b164 = imagen[:, :, 164].squeeze() * factor

    leaf  = remove_small_holes(b10 < 2000, area_threshold=200)
    drops = (b164 >= 3300) & (b164 <= 4150)

    return leaf, drops


def _trinarizar(leaf, drops, color_drops=(255, 0, 0)):
    """Construye imagen trinarizada (R,G,B) a partir de las máscaras."""
    h, w = leaf.shape
    out = np.zeros((h, w, 3), dtype=np.uint8)
    out[leaf]  = [0, 255, 0]           # verde → hoja
    out[drops] = list(color_drops)     # rojo por defecto → gotas
    return out


# -------------------------------------------------------------------
# Utilidades generales
# -------------------------------------------------------------------
def band_idx(im, wl):
    """
    Índice de la banda cuya longitud de onda central es más
    cercana a `wl` (en nm).
    """
    centers = np.array([float(x) for x in im.bands.centers])
    return int(np.abs(centers - wl).argmin())


def to_rgb(im, wl_r=639.1, wl_g=548.4, wl_b=459.2):
    """
    Pasa un cubo hiperespectral a una imagen RGB de contraste normalizado.

    Parámetros
    ----------
    im : spectral.Image
    wl_r, wl_g, wl_b : float
        Longitudes de onda (nm) para las bandas R, G y B.
    """
    b = cv2.normalize(
        im.read_band(band_idx(im, wl_b)),
        None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U
    )
    g = cv2.normalize(
        im.read_band(band_idx(im, wl_g)),
        None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U
    )
    r = cv2.normalize(
        im.read_band(band_idx(im, wl_r)),
        None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U
    )

    img = cv2.merge([b, g, r]).astype(np.float32)

    # Balance de blancos sencillo
    B, G, R = cv2.split(img)
    mean_lum = (B.mean() + G.mean() + R.mean()) / 3
    for ch in (B, G, R):
        ch *= mean_lum / (ch.mean() + 1e-8)

    return np.clip(cv2.merge([B, G, R]), 0, 255).astype(np.uint8)


def estimar_transformacion_por_extremos(leaf_sin, leaf_con):
    """
    Estima una transformación euclídea (escala + rotación + traslación)
    que alinee la hoja `leaf_sin` sobre `leaf_con` usando los extremos
    de la hoja (arriba/abajo).

    Devuelve
    --------
    R0 : np.ndarray shape (2, 2)
        Matriz de rotación * escala.
    t0 : np.ndarray shape (2,)
        Traslación.
    """
    ys_s, xs_s = np.where(leaf_sin)
    ys_c, xs_c = np.where(leaf_con)

    # Si no hay puntos, devolvemos identidad
    if len(xs_s) == 0 or len(xs_c) == 0:
        return np.eye(2, dtype=np.float32), np.zeros(2, dtype=np.float32)

    p1_s = np.array([xs_s[ys_s.argmin()], ys_s.min()], dtype=np.float32)
    p2_s = np.array([xs_s[ys_s.argmax()], ys_s.max()], dtype=np.float32)
    p1_c = np.array([xs_c[ys_c.argmin()], ys_c.min()], dtype=np.float32)
    p2_c = np.array([xs_c[ys_c.argmax()], ys_c.max()], dtype=np.float32)

    v_s, v_c = p2_s - p1_s, p2_c - p1_c
    len_s, len_c = np.linalg.norm(v_s), np.linalg.norm(v_c)

    scale0 = (len_c / len_s) if len_s else 1.0
    theta0 = math.atan2(v_c[1], v_c[0]) - math.atan2(v_s[1], v_s[0])

    R0 = np.array(
        [
            [scale0 * math.cos(theta0), -scale0 * math.sin(theta0)],
            [scale0 * math.sin(theta0),  scale0 * math.cos(theta0)],
        ],
        dtype=np.float32,
    )
    t0 = p1_c - R0 @ p1_s
    return R0, t0


def matriz_transformacion(R0, t0, scale_adj=1.0, rot_deg=0.0, dx=0, dy=0):
    """Aplica ajustes de usuario sobre la transformación base."""
    R1 = R0 * scale_adj
    rad = math.radians(rot_deg)
    Rr = np.array(
        [[math.cos(rad), -math.sin(rad)], [math.sin(rad), math.cos(rad)]],
        dtype=np.float32,
    )
    Rf = Rr @ R1
    tf = t0 + np.array([dx, dy], dtype=np.float32)
    return np.hstack([Rf, tf.reshape(2, 1)])


def warp_mask(mask, M, shape):
    """Aplica la matriz afín `M` sobre `mask` (bool) devolviendo bool."""
    h, w = shape
    return cv2.warpAffine(
        mask.astype(np.uint8),
        M,
        (w, h),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
    ).astype(bool)


def trinarizar_final(leaf_con, drop_con, drop_sin_aligned, min_px=75):
    """
    Genera trinarizada definitiva eliminando gotas comunes.

    Verde  : hoja.
    Rojo   : gotas únicas (tamaño ≥ min_px).
    """
    resta  = drop_con & ~drop_sin_aligned
    limpia = remove_small_objects(resta, min_size=min_px)

    h, w = leaf_con.shape
    out = np.zeros((h, w, 3), dtype=np.uint8)
    out[leaf_con] = [0, 255, 0]
    out[limpia]   = [255, 0, 0]
    return out


# -------------------------------------------------------------------
# Procesamientos principales
# -------------------------------------------------------------------
def aplicar_procesamiento_dual(img_con, img_sin):
    """
    Flujo completo SIN/CON con alineación por ECC.

    Devuelve imagen trinarizada (verde=hoja común, rojo=gotas únicas).
    """
    # 1) Máscaras crudas
    leaf_con, drops_con_raw = _obtener_mascaras(img_con)
    leaf_sin, drops_sin_raw = _obtener_mascaras(img_sin)

    # 2) Recorte al área común
    filas = min(leaf_con.shape[0], leaf_sin.shape[0])
    cols  = min(leaf_con.shape[1], leaf_sin.shape[1])

    leaf_con      = leaf_con[:filas, :cols]
    drops_con_raw = drops_con_raw[:filas, :cols]
    leaf_sin      = leaf_sin[:filas, :cols]
    drops_sin_raw = drops_sin_raw[:filas, :cols]

    # 3) Alineación ECC (rot+trasl)
    ref = leaf_con.astype(np.float32)
    mov = leaf_sin.astype(np.float32)
    warp_mat = np.eye(2, 3, dtype=np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 50, 1e-6)

    try:
        cv2.findTransformECC(ref, mov, warp_mat, cv2.MOTION_EUCLIDEAN, criteria)
    except cv2.error:
        warp_mat = np.eye(2, 3, dtype=np.float32)   # si falla, identidad

    # 4) Warp de la máscara de gotas SIN
    drops_sin_reg = cv2.warpAffine(
        drops_sin_raw.astype(np.uint8),
        warp_mat,
        (cols, filas),
        flags=cv2.INTER_NEAREST,
    ).astype(bool)

    # 5) Hoja común y gotas restringidas
    hoja_comun = leaf_con & cv2.warpAffine(
        leaf_sin.astype(np.uint8), warp_mat, (cols, filas),
        flags=cv2.INTER_NEAREST,
    ).astype(bool)

    gotas_con = drops_con_raw & hoja_comun
    gotas_sin = drops_sin_reg & hoja_comun

    gotas_final = gotas_con & ~gotas_sin

    # 6) Trinarizada
    return _trinarizar(hoja_comun, gotas_final)


def aplicar_procesamiento(imagen):
    """
    Versión rápida (no dual): trinariza una sola imagen.
    """
    leaf, drops_raw = _obtener_mascaras(imagen)
    drops = drops_raw & leaf
    return _trinarizar(leaf, drops)


def realizar_post_procesamiento(trinarizada):
    """
    Hook para procesamiento extra si se necesitase. Ahora identidad.
    """
    return trinarizada
