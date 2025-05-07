# src/funciones/__init__.py

from .archivos import limpiar_carpeta, guardar_archivos_subidos
from .procesamiento import (
    estimar_transformacion_por_extremos,
    matriz_transformacion,
    warp_mask,
    band_idx,
    to_rgb,
    aplicar_procesamiento_dual,
    aplicar_procesamiento,
    realizar_post_procesamiento,
    trinarizar_final
    # _obtener_mascaras and _trinarizar are conventionally private and not re-exported.
)
from .alignment import (
    compute_affine_transform,
    align_and_substract
)
from .csv import generar_datos_csv
from .interfaz import cargar_hyper_bin

# Alias para compatibilidad con imports antiguos
# Ensure these aliases point to functions that are actually being exported above.
# For example, if procesar_datos was intended to be trinarizar_final, that would be an issue.
procesar_datos = aplicar_procesamiento_dual
procesar_datos_csv = generar_datos_csv
