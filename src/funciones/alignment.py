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
        limbo,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    )
    return limbo

# --------------------------------------------------
# Detección y emparejamiento de puntos ORB
# --------------------------------------------------
def _detect_and_match(img1: np.ndarray, img2: np.ndarray, nfeatures: int = 4000) -> tuple[np.ndarray, np.ndarray]:
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
def compute_affine_transform(edges1: np.ndarray,
                             edges2: np.ndarray,
                             reproj_thresh: float = 3.0,
                             max_iters: int = 5000,
                             confidence: float = 0.995) -> np.ndarray:
    pts1, pts2 = _detect_and_match(edges1, edges2)
    if len(pts1) < 10:
        raise RuntimeError("Pocos matches para calcular transform_affine")
    M, _ = cv2.estimateAffinePartial2D(
        pts2, pts1,
        method=cv2.RANSAC,
        ransacReprojThreshold=reproj_thresh,
        maxIters=max_iters,
        confidence=confidence
    )
    if M is None:
        raise RuntimeError("No pudo estimarse la matriz afín")
    return M

# --------------------------------------------------
# Función principal de alineación y sustracción
# --------------------------------------------------
def align_and_substract(img_no_drops: np.ndarray,
                        img_with_drops: np.ndarray,
                        mask_no_drops: np.ndarray,
                        mask_with_drops: np.ndarray,
                        canny_low: int = 50,
                        canny_high: int = 150,
                        thresh_val: int = 25,
                        morph_kernel_size: tuple[int, int] = (5, 5),
                        debug: bool = False
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
    M = compute_affine_transform(edges1, edges2)

    # 4) Warp de la máscara CON gotas
    h, w = mask_no_drops.shape
    aligned_mask = cv2.warpAffine(
        mask_with_drops, M, (w, h),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT, borderValue=0
    )

    # 5) (Opcional) Detección de diferencias como mapa de debug
    #    Se puede omitir en la interfaz si no se usa
    aligned_img = cv2.warpAffine(
        img_with_drops, M, (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT, borderValue=0
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
