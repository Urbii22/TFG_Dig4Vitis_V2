from __future__ import annotations

from collections.abc import Callable

TRANSLATIONS: dict[str, dict[str, str]] = {
    "es": {
        "app_title": "EcoVid",
        "subtitle": "Herramienta para la segmentación de imágenes hiperespectrales y detección de cobre en viñedos.",
        "tab_process": " Cargar y Procesar Imágenes ",
        "tab_about": " Acerca del TFG ",
        "analysis_header": "Análisis de Imágenes",
        "upload_sin": "Imagen de referencia SIN tratamiento (.bil + .hdr)",
        "upload_con": "Imagen CON tratamiento (.bil + .hdr)",
        "start": "🚀 Iniciar Procesamiento",
        "processing": "Analizando imágenes... Por favor, espere.",
        "error_missing": "Error: Asegúrate de subir los archivos .hdr y .bil para ambas imágenes.",
        "error_mismatch": "Error: Los identificadores de muestra en los nombres de archivo no coinciden.",
        "processed_ok": "¡Procesamiento completado con éxito!",
    },
    "en": {
        "app_title": "EcoVid",
        "subtitle": "Tool for hyperspectral image segmentation and copper detection in vineyards.",
        "tab_process": " Upload and Process Images ",
        "tab_about": " About the Project ",
        "analysis_header": "Image Analysis",
        "upload_sin": "Reference image WITHOUT treatment (.bil + .hdr)",
        "upload_con": "Image WITH treatment (.bil + .hdr)",
        "start": "🚀 Start Processing",
        "processing": "Analyzing images... Please wait.",
        "error_missing": "Error: Please upload both .hdr and .bil files for each image.",
        "error_mismatch": "Error: Sample identifiers from filenames do not match.",
        "processed_ok": "Processing completed successfully!",
    },
}


def get_translator(lang: str) -> Callable[[str], str]:
    table = TRANSLATIONS.get(lang, TRANSLATIONS["es"])  # default es

    def t(key: str) -> str:
        return table.get(key, key)

    return t
