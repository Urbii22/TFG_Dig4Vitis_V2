import cv2
import numpy as np


# --------------------------------------------------
# Eliminación de pecíolo (solo limbo)
# --------------------------------------------------
def _remove_petiole(mask: np.ndarray, ksize: tuple[int, int] = (5, 50)) -> np.ndarray:
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, ksize)
    opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    num, labels, stats, _ = cv2.connectedComponentsWithStats(opened, connectivity=8)
    if num <= 1:
        return opened
    largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    limbo = np.where(labels == largest, 255, 0).astype(np.uint8)
    limbo = cv2.morphologyEx(
        limbo, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    )
    return limbo


# --------------------------------------------------
# Detección y emparejamiento de puntos ORB
# --------------------------------------------------
def _detect_and_match(
    img1: np.ndarray, img2: np.ndarray, nfeatures: int = 4000
) -> tuple[np.ndarray, np.ndarray]:
    orb = cv2.ORB_create(nfeatures=nfeatures)
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    knn = bf.knnMatch(des1, des2, k=2)
    good = [m for m, n in knn if m.distance < 0.75 * n.distance]
    pts1 = np.float32([kp1[m.queryIdx].pt for m in good])
    pts2 = np.float32([kp2[m.trainIdx].pt for m in good])
    return pts1, pts2


# --------------------------------------------------
# Estimación de la transformación afín por RANSAC
# --------------------------------------------------
def compute_affine_transform(
    edges1: np.ndarray,
    edges2: np.ndarray,
    reproj_thresh: float = 3.0,
    max_iters: int = 5000,
    confidence: float = 0.995,
    nfeatures: int = 4000,  # Nuevo parámetro para nfeatures de ORB
    detection_scale_factor: float = 1.0,  # Nuevo parámetro para escalado
    return_metrics: bool = False,
) -> np.ndarray | tuple[np.ndarray, dict]:

    current_reproj_thresh = reproj_thresh

    if detection_scale_factor < 1.0 and detection_scale_factor > 0.0:
        # Escalar imágenes para detección
        h1, w1 = edges1.shape[:2]
        edges1_proc = cv2.resize(
            edges1,
            (int(w1 * detection_scale_factor), int(h1 * detection_scale_factor)),
            interpolation=cv2.INTER_AREA,
        )
        h2, w2 = edges2.shape[:2]
        edges2_proc = cv2.resize(
            edges2,
            (int(w2 * detection_scale_factor), int(h2 * detection_scale_factor)),
            interpolation=cv2.INTER_AREA,
        )
        # Ajustar el umbral de reproyección para las imágenes escaladas
        current_reproj_thresh = reproj_thresh * detection_scale_factor
    else:
        edges1_proc = edges1
        edges2_proc = edges2
        # detection_scale_factor es efectivamente 1.0 para los cálculos si no se escala

    # Detección y emparejamiento de puntos en las imágenes procesadas (posiblemente escaladas)
    pts1_matched, pts2_matched = _detect_and_match(edges1_proc, edges2_proc, nfeatures=nfeatures)

    if len(pts1_matched) < 10:
        raise RuntimeError(
            f"Pocos matches ({len(pts1_matched)}) para calcular transform_affine. Considere ajustar nfeatures o detection_scale_factor."
        )

    # M_estimated transforma coordenadas del espacio de edges2_proc al espacio de edges1_proc
    # pts2_matched (de edges2_proc) son origen, pts1_matched (de edges1_proc) son destino.
    M_estimated, inliers_mask = cv2.estimateAffinePartial2D(
        pts2_matched,
        pts1_matched,
        method=cv2.RANSAC,
        ransacReprojThreshold=current_reproj_thresh,  # Usar umbral posiblemente escalado
        maxIters=max_iters,
        confidence=confidence,
    )

    if M_estimated is None:
        raise RuntimeError("No pudo estimarse la matriz afín")

    # Ajustar traslación si se trabajó a escala
    if detection_scale_factor < 1.0 and detection_scale_factor > 0.0:
        final_M = M_estimated.copy()
        final_M[0, 2] /= detection_scale_factor
        final_M[1, 2] /= detection_scale_factor
    else:
        final_M = M_estimated

    if not return_metrics:
        return final_M

    # Cálculo de métricas de alineación
    n_matches = len(pts1_matched)
    n_inliers = int(inliers_mask.sum()) if inliers_mask is not None else 0
    inlier_ratio = (n_inliers / n_matches) if n_matches > 0 else 0.0

    # Error medio de reproyección (en píxeles originales aproximados)
    if inliers_mask is not None and n_inliers > 0:
        inliers_bool = inliers_mask.ravel().astype(bool)
        pts2_in = pts2_matched[inliers_bool]
        pts1_in = pts1_matched[inliers_bool]
        # Reproyectar pts2 -> espacio de pts1
        ones = np.ones((pts2_in.shape[0], 1), dtype=np.float32)
        pts2_aug = np.hstack([pts2_in, ones])
        warped = (pts2_aug @ M_estimated.T).astype(np.float32)
        diffs = warped - pts1_in
        err = np.sqrt((diffs**2).sum(axis=1))
        mean_err_scaled = float(err.mean())
        mean_err = (
            mean_err_scaled / detection_scale_factor
            if detection_scale_factor > 0
            else mean_err_scaled
        )
    else:
        mean_err = float("nan")

    metrics = {
        "n_matches": n_matches,
        "n_inliers": n_inliers,
        "inlier_ratio": inlier_ratio,
        "mean_reproj_error_px": mean_err,
        "orb_nfeatures": nfeatures,
        "scale_factor": detection_scale_factor,
        "ransac_reproj_thresh": reproj_thresh,
        "ransac_max_iters": max_iters,
        "ransac_confidence": confidence,
    }

    return final_M, metrics


# --------------------------------------------------
# Función principal de alineación y sustracción
# --------------------------------------------------
def align_and_substract(
    img_no_drops: np.ndarray,
    img_with_drops: np.ndarray,
    mask_no_drops: np.ndarray,
    mask_with_drops: np.ndarray,
    canny_low: int = 50,
    canny_high: int = 150,
    thresh_val: int = 25,
    morph_kernel_size: tuple[int, int] = (5, 5),
    debug: bool = False,
    # Nuevos parámetros para eficiencia y control
    orb_nfeatures: int = 4000,
    detection_scale_factor: float = 1.0,  # 1.0 para comportamiento original
    ransac_reproj_thresh: float = 3.0,
    ransac_max_iters: int = 5000,
    ransac_confidence: float = 0.995,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Alinea la máscara CON gotas sobre la SIN gotas (usando solo contornos de hoja)
    y devuelve:
      - M: matriz 2x3 de la transformación afín
      - aligned_mask: máscara de hoja CON gotas alineada sobre SIN
      - diff_mask: mapa binario de diferencias (solo para debug, se puede ignorar)
    """
    # 1) Limbo puro de ambas máscaras
    limbo1 = _remove_petiole(mask_no_drops)
    limbo2 = _remove_petiole(mask_with_drops)

    # 2) Bordes (Canny)
    edges1 = cv2.Canny(limbo1, canny_low, canny_high)
    edges2 = cv2.Canny(limbo2, canny_low, canny_high)

    # 3) Estimación afín
    M = compute_affine_transform(
        edges1,
        edges2,
        reproj_thresh=ransac_reproj_thresh,
        max_iters=ransac_max_iters,
        confidence=ransac_confidence,
        nfeatures=orb_nfeatures,
        detection_scale_factor=detection_scale_factor,
    )

    # 4) Warp de la máscara CON gotas
    h, w = mask_no_drops.shape
    aligned_mask = cv2.warpAffine(
        mask_with_drops,
        M,
        (w, h),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )

    # 5) (Opcional) Detección de diferencias como mapa de debug
    #    Se puede omitir en la interfaz si no se usa
    aligned_img = cv2.warpAffine(
        img_with_drops,
        M,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    diff = cv2.absdiff(img_no_drops, aligned_img)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, diff_mask = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, morph_kernel_size)
    diff_mask = cv2.morphologyEx(diff_mask, cv2.MORPH_OPEN, kernel)
    diff_mask = cv2.morphologyEx(diff_mask, cv2.MORPH_CLOSE, kernel)

    if debug:
        cv2.imshow("Limbo SIN", limbo1)
        cv2.imshow("Limbo CON", limbo2)
        cv2.imshow("Hoja alineada", aligned_mask)
        cv2.imshow("Mapa diff", diff_mask)
        cv2.waitKey(0)

    return M, aligned_mask, diff_mask
