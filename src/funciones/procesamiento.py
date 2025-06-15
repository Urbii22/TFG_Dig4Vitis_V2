import math
import cv2
import numpy as np
from spectral.io import envi
from skimage.morphology import (
    remove_small_holes,
    remove_small_objects,
)
# Import alignment functions
from .alignment import _remove_petiole, compute_affine_transform

# -------------------------------------------------------------------
# Máscaras básicas
# -------------------------------------------------------------------
def _obtener_mascaras(imagen):
    """
    Calcula dos máscaras binarias a partir del cubo hiperespectral:

    Returns
    -------
    leaf  : np.ndarray[bool]  # Máscara de la hoja (región verde).
    drops : np.ndarray[bool]  # Máscara de gotas sin limitar a la hoja.
    """
    factor = 10000
    b10  = imagen[:, :, 9].squeeze()   * factor
    b164 = imagen[:, :, 164].squeeze() * factor

    leaf  = remove_small_holes(b10 < 2000, area_threshold=200)
    
    #cuprocol
    
    #drops = ((b164 >= 3900) & (b164 <= 4100)) | ((b164 >= 4900) & (b164 <= 5200))
    
    #cuporantol duo
    
    drops = ((b164 >= 3900) & (b164 <= 4300)) | ((b164 >= 4900) & (b164 <= 5200))
    

    
    return leaf, drops


def _trinarizar(leaf, drops, color_drops=(255, 0, 0)):
    """Construye imagen trinarizada (R,G,B) a partir de las máscaras."""
    h, w = leaf.shape
    out = np.zeros((h, w, 3), dtype=np.uint8)
    out[leaf]  = [0, 255, 0]           # verde → hoja
    out[drops] = list(color_drops)     # rojo → gotas
    return out

def trinarizar_final(leaf_mask: np.ndarray,
                     current_drops_mask: np.ndarray,
                     aligned_drops_to_subtract_mask: np.ndarray,
                     min_drop_size: int = 1) -> np.ndarray:
    """
    Genera una imagen trinarizada (hoja, gotas únicas) eliminando las gotas
    presentes en `aligned_drops_to_subtract_mask` de `current_drops_mask`.
    Las gotas resultantes se filtran por tamaño (si min_drop_size > 0).
    """
    # Asegurarse de que las gotas estén solo sobre la hoja
    # current_drops_mask should already be drops on leaf if prepared correctly by caller
    effective_drops = current_drops_mask & leaf_mask
    
    # Restar las gotas alineadas de la imagen de referencia (si las hay)
    unique_drops = effective_drops & ~aligned_drops_to_subtract_mask
    
    # Eliminar pequeños artefactos de las gotas únicas
    if min_drop_size > 0:
        # remove_small_objects expects a boolean array
        cleaned_unique_drops = remove_small_objects(unique_drops.astype(bool), min_size=min_drop_size)
    else:
        cleaned_unique_drops = unique_drops
        
    return _trinarizar(leaf_mask, cleaned_unique_drops)

# -------------------------------------------------------------------
# Utilidades de transformación manual
# -------------------------------------------------------------------
def estimar_transformacion_por_extremos(leaf_sin: np.ndarray,
                                       leaf_con: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    # ... (igual que antes) ...
    ys_s, xs_s = np.where(leaf_sin)
    ys_c, xs_c = np.where(leaf_con)
    if len(xs_s) == 0 or len(xs_c) == 0:
        return np.eye(2, dtype=np.float32), np.zeros(2, dtype=np.float32)
    p1_s = np.array([xs_s[ys_s.argmin()], ys_s.min()], dtype=np.float32)
    p2_s = np.array([xs_s[ys_s.argmax()], ys_s.max()], dtype=np.float32)
    p1_c = np.array([xs_c[ys_c.argmin()], ys_c.min()], dtype=np.float32)
    p2_c = np.array([xs_c[ys_c.argmax()], ys_c.max()], dtype=np.float32)
    v_s = p2_s - p1_s
    v_c = p2_c - p1_c
    len_s = np.linalg.norm(v_s)
    len_c = np.linalg.norm(v_c)
    scale0 = (len_c / len_s) if len_s else 1.0
    theta0 = math.atan2(v_c[1], v_c[0]) - math.atan2(v_s[1], v_s[0])
    R0 = np.array([
        [scale0 * math.cos(theta0), -scale0 * math.sin(theta0)],
        [scale0 * math.sin(theta0),  scale0 * math.cos(theta0)],
    ], dtype=np.float32)
    t0 = p1_c - R0 @ p1_s
    return R0, t0


def matriz_transformacion(R0: np.ndarray,
                          t0: np.ndarray,
                          scale_adj: float = 1.0,
                          rot_deg: float = 0.0,
                          dx: int = 0,
                          dy: int = 0) -> np.ndarray:
    # ... (igual que antes) ...
    R1 = R0 * scale_adj
    rad = math.radians(rot_deg)
    Rr = np.array([[math.cos(rad), -math.sin(rad)],
                   [math.sin(rad),  math.cos(rad)]], dtype=np.float32)
    Rf = Rr @ R1
    tf = t0 + np.array([dx, dy], dtype=np.float32)
    return np.hstack([Rf, tf.reshape(2, 1)])


def warp_mask(mask: np.ndarray,
              M: np.ndarray,
              shape: tuple[int, int]) -> np.ndarray:
    """
    Aplica warpAffine a una máscara binaria (uint8 o bool), devuelve bool.
    """
    h, w = shape
    warped = cv2.warpAffine(
        mask.astype(np.uint8), M, (w, h),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT, borderValue=0
    )
    return warped.astype(bool)

# -------------------------------------------------------------------
# Máscaras y RGB
# -------------------------------------------------------------------
def band_idx(im, wl: float) -> int:
    centers = np.array([float(x) for x in im.bands.centers])
    return int(np.abs(centers - wl).argmin())


def to_rgb(im, wl_r: float = 639.1,
           wl_g: float = 548.4,
           wl_b: float = 459.2) -> np.ndarray:
    # ... (igual que antes) ...
    b = cv2.normalize(im.read_band(band_idx(im, wl_b)),
                      None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    g = cv2.normalize(im.read_band(band_idx(im, wl_g)),
                      None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    r = cv2.normalize(im.read_band(band_idx(im, wl_r)),
                      None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    img = cv2.merge([b, g, r]).astype(np.float32)
    B, G, R = cv2.split(img)
    mean_lum = (B.mean() + G.mean() + R.mean()) / 3
    for ch in (B, G, R):
        ch *= mean_lum / (ch.mean() + 1e-8)
    return np.clip(cv2.merge([B, G, R]), 0, 255).astype(np.uint8)

# -------------------------------------------------------------------
# Procesamientos principales
# -------------------------------------------------------------------
def aplicar_procesamiento_dual(img_con: np.ndarray,
                               img_sin: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, tuple[int, int], np.ndarray, np.ndarray]:
    """
    Flujo completo SIN/CON con alineación por ORB/RANSAC.

    Devuelve:
      - trinarizada: imagen trinarizada (verde=hoja común, rojo=gotas únicas).
      - leaf_con_cropped: máscara de hoja CON gotas, recortada al área común.
      - leaf_sin_aligned: máscara de hoja SIN gotas, recortada y alineada a CON.
      - common_shape: tupla (filas, cols) del área común.
      - hoja_comun: máscara booleana de la hoja común después de la alineación.
      - gotas_final: máscara booleana de las gotas finales sobre la hoja común.
    """
    # 1) Máscaras crudas
    leaf_con, drops_con_raw = _obtener_mascaras(img_con)
    leaf_sin, drops_sin_raw = _obtener_mascaras(img_sin)

    # 2) Recorte al área común
    filas = min(leaf_con.shape[0], leaf_sin.shape[0])
    cols  = min(leaf_con.shape[1], leaf_sin.shape[1])

    leaf_con_cropped = leaf_con[:filas, :cols]
    drops_con_raw_cropped = drops_con_raw[:filas, :cols]
    leaf_sin_cropped = leaf_sin[:filas, :cols]
    drops_sin_raw_cropped = drops_sin_raw[:filas, :cols]

    # 3) Alineación por ORB/RANSAC
    warp_mat = np.eye(2, 3, dtype=np.float32) # Default to identity

    try:
        # Convert boolean masks to uint8 (0/255) for alignment functions
        leaf_con_u8 = (leaf_con_cropped * 255).astype(np.uint8)
        leaf_sin_u8 = (leaf_sin_cropped * 255).astype(np.uint8)

        # Isolate limbos (leaf blades without petiole)
        limbo_con = _remove_petiole(leaf_con_u8)
        limbo_sin = _remove_petiole(leaf_sin_u8)

        # Detect edges using Canny
        # Using fixed thresholds, consider making them parameters if needed
        edges_con = cv2.Canny(limbo_con, 50, 150)
        edges_sin = cv2.Canny(limbo_sin, 50, 150)

        # Compute affine transform (aligns sin to con)
        # compute_affine_transform(edges_ref, edges_to_align)
        # M transforms edges_to_align to align with edges_ref
        warp_mat = compute_affine_transform(edges_con, edges_sin)
        
    except RuntimeError as e:
        print(f"Alignment failed: {e}. Using identity matrix.")
        # warp_mat remains identity if alignment fails
        pass # Or st.warning if streamlit is available here, but better to keep processing logic clean
    except cv2.error as e: # Catch potential OpenCV errors during Canny or other CV ops
        print(f"OpenCV error during alignment: {e}. Using identity matrix.")
        pass


    # 4) Warp de la máscara de gotas SIN y la máscara de hoja SIN
    drops_sin_aligned = cv2.warpAffine(
        drops_sin_raw_cropped.astype(np.uint8), # Ensure uint8 for warp
        warp_mat,
        (cols, filas),
        flags=cv2.INTER_NEAREST,
    ).astype(bool)

    leaf_sin_aligned = cv2.warpAffine(
        leaf_sin_cropped.astype(np.uint8), # Ensure uint8 for warp
        warp_mat, 
        (cols, filas),
        flags=cv2.INTER_NEAREST,
    ).astype(bool)

    # 5) Hoja común y gotas restringidas
    # Hoja común is the intersection of the original CON leaf and the aligned SIN leaf
    hoja_comun = leaf_con_cropped & leaf_sin_aligned

    # Restrict drops to this common leaf area
    gotas_con = drops_con_raw_cropped & hoja_comun
    # Ensure drops_sin_aligned are also restricted to the common leaf area
    # (though alignment should ideally place them within leaf_con_cropped if original drops were on leaf_sin_cropped)
    gotas_sin = drops_sin_aligned & hoja_comun 
    
    gotas_final = gotas_con & ~gotas_sin

    # 6) Trinarizada final
    trinarizada_result = _trinarizar(hoja_comun, gotas_final)
    
    # Return leaf_con_cropped (original CON mask, cropped) and leaf_sin_aligned (SIN mask, cropped and warped)
    # for visualization purposes.
    return trinarizada_result, leaf_con_cropped, leaf_sin_aligned, (filas, cols), hoja_comun, gotas_final


def aplicar_procesamiento(imagen: np.ndarray) -> np.ndarray:
    """Trinariza una sola imagen sin comparación dual."""
    leaf, drops_raw = _obtener_mascaras(imagen)
    drops = drops_raw & leaf
    return _trinarizar(leaf, drops)


def realizar_post_procesamiento(trinarizada: np.ndarray) -> np.ndarray:
    """Hook para procesamiento extra; devuelve la trinarizada sin cambios."""
    return trinarizada
