import spectral
import numpy as np
from skimage.morphology import remove_small_objects, remove_small_holes, disk, opening, closing
from skimage.measure import label, regionprops
import math

def aplicar_procesamiento(imagen):
    """
    Realiza el análisis de la imagen hiperespectral utilizando la nueva versión de procesamiento:
      - Se utiliza la Banda 10 (índice 9) para la detección de la hoja (píxeles con valor < 2000).
      - Se utiliza la Banda 164 (índice 163) para la detección de gotas (píxeles en el rango [3500, 4000]).
      - Se aplican operaciones morfológicas para reducir el ruido y se filtran las gotas en función de su circularidad.
    
    Parámetros:
      imagen: objeto de imagen hiperespectral (resultado de spectral.open_image).
      modo_umbral: parámetro heredado (en la nueva versión se ignora).
    
    Retorna:
      Imagen trinarizada (array RGB uint8) donde:
        - Fondo es negro.
        - Hoja sin gotas es verde ([0,255,0]).
        - Gotas son rojas ([255,0,0]).
    """
    # Factor para recuperar el rango original (0-10000)
    factor = 10000

    # Extraer la Banda 10 y la Banda 164
    banda_10 = imagen[:, :, 9].squeeze() * factor
    banda_164 = imagen[:, :, 164].squeeze() * factor

    # Crear la máscara de la hoja: píxeles con valor < 2000 en la Banda 10
    leaf_mask = (banda_10 < 2000)
    leaf_mask = remove_small_holes(leaf_mask, area_threshold=200)

    # Detección inicial de gotas en la Banda 164 (rango [4092, 4558]) y restringir a la zona de la hoja
    mask_droplets = ((banda_164 >= 4150) & (banda_164 <= 4450) ) | ((banda_164 >= 5000) & (banda_164 <= 5100))| ((banda_164 >= 5700) & (banda_164 <= 6000)) | ((banda_164 >= 7000) & (banda_164 <= 10000))

    # mask_droplets = ((banda_164 >= 4092) & (banda_164 <= 4558) ) 

    mask_droplets = mask_droplets & leaf_mask
 
     # Crear imagen trinarizada: fondo negro, hoja verde y gotas rojas
    filas, columnas = banda_10.shape
    trinarizada = np.zeros((filas, columnas, 3), dtype=np.uint8)
    trinarizada[leaf_mask] = [0, 255, 0]         # Hoja
    trinarizada[mask_droplets] = [255, 0, 0] # Gotas

    return trinarizada

def realizar_post_procesamiento(trinarizada):
    """
    Función de post-procesamiento de la imagen trinarizada.
    En esta nueva versión no se requiere realizar modificaciones adicionales,
    por lo que se retorna la imagen tal y como ha sido procesada.
    """
    return trinarizada
