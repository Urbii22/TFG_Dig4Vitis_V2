import cv2
import numpy as np
from skimage import measure

def aplicar_procesamiento(imagen, modo_umbral="Fijo"):
    """
    Aplica el procesamiento de trinarización utilizando:
    - Banda 30 para detección de hoja (binarizada automáticamente con Otsu)
    - Banda 60 para detección de cuprocol, usando umbral fijo o adaptativo
    """
    # Procesar banda para detección de hoja (Banda 30)
    banda_hoja = imagen.read_band(30)
    banda_hoja = cv2.normalize(banda_hoja, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    _, hoja_bin = cv2.threshold(banda_hoja, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Procesar banda para detección de cuprocol (Banda 60)
    banda_cuprocol = imagen.read_band(60)
    banda_cuprocol = cv2.normalize(banda_cuprocol, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    
    if modo_umbral == "Fijo":
        cupro_min = int(50 * 255 / 1000)
        cupro_max = int(800 * 255 / 1000)
    else:
        tolerancia = 0.10
        mejor_T = 0
        max_detectados = -1
        for T_candidate in range(0, 256):
            cupro_min_candidate = int(max(0, T_candidate * (1 - tolerancia)))
            cupro_max_candidate = int(min(255, T_candidate * (1 + tolerancia)))
            mask_candidate = cv2.inRange(banda_cuprocol, cupro_min_candidate, cupro_max_candidate)
            num_detectados = np.count_nonzero(mask_candidate)
            if num_detectados > max_detectados:
                max_detectados = num_detectados
                mejor_T = T_candidate
        cupro_min = int(max(0, mejor_T * (1 - tolerancia)))
        cupro_max = int(min(255, mejor_T * (1 + tolerancia)))
    
    gotas_bin = cv2.inRange(banda_cuprocol, cupro_min, cupro_max)
    
    trinarizada = np.zeros((banda_hoja.shape[0], banda_hoja.shape[1], 3), dtype=np.uint8)
    trinarizada[(hoja_bin == 0) & (gotas_bin == 0)] = [255, 0, 0]
    trinarizada[(hoja_bin == 0) & (gotas_bin == 255)] = [0, 255, 0]
    trinarizada[hoja_bin == 255] = [0, 0, 0]
    
    return trinarizada

def realizar_post_procesamiento(trinarizada):
    """Realiza el post-procesamiento de la imagen trinarizada."""
    mascara_cobre = (trinarizada[:, :, 0] == 255) & (trinarizada[:, :, 1] == 0) & (trinarizada[:, :, 2] == 0)
    mascara_dilatada = cv2.dilate(mascara_cobre.astype(np.uint8), 
                                   np.ones((5, 5), np.uint8), iterations=1)
    mascara_rellenada = cv2.morphologyEx(mascara_dilatada, cv2.MORPH_CLOSE, 
                                          np.ones((5, 5), np.uint8))
    mascara_final = cv2.erode(mascara_rellenada, 
                              np.ones((3, 3), np.uint8), iterations=1)
    
    etiquetas = measure.label(mascara_final, connectivity=2)
    propiedades = measure.regionprops(etiquetas)
    
    area_min_umbral = 100
    area_max_umbral = 500
    
    trinarizada[(mascara_final == 1) & ~mascara_cobre] = [255, 0, 0]
    for prop in propiedades:
        if prop.area > area_max_umbral or prop.area < area_min_umbral:
            for coord in prop.coords:
                trinarizada[coord[0], coord[1]] = [0, 255, 0]
    return trinarizada
