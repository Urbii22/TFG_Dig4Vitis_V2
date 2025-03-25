import os
import logging
import atexit
import streamlit as st
import cv2
import numpy as np
import spectral

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

UPLOAD_FOLDER = 'archivos_subidos'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def limpiar_carpeta():
    logging.info("Limpiando carpeta de archivos subidos.")
    for archivo in os.listdir(UPLOAD_FOLDER):
        ruta_archivo = os.path.join(UPLOAD_FOLDER, archivo)
        try:
            os.unlink(ruta_archivo)
        except Exception as e:
            logging.error(f"Error al eliminar {ruta_archivo}: {e}")

atexit.register(limpiar_carpeta)

def validar_archivos_hiperespectrales(archivos):
    if len(archivos) != 2:
        st.error("Debes subir exactamente dos archivos: un .bil y un .bil.hdr.")
        return None, None, None
    bil_file = None
    hdr_file = None
    base_name = None
    for archivo in archivos:
        if archivo.name.endswith('.bil.hdr'):
            hdr_file = archivo
            base_name = os.path.splitext(os.path.splitext(archivo.name)[0])[0]
        elif archivo.name.endswith('.bil'):
            bil_file = archivo
            temp_base = os.path.splitext(archivo.name)[0]
            if base_name and base_name != temp_base:
                st.error("Los archivos no corresponden a la misma imagen.")
                return None, None, None
            base_name = temp_base
        else:
            st.error("Formato de archivo no soportado.")
            return None, None, None
    if not (bil_file and hdr_file):
        st.error("Faltan archivos necesarios (.bil y .bil.hdr).")
    return hdr_file, bil_file, base_name

def guardar_archivo(archivo):
    ruta = os.path.join(UPLOAD_FOLDER, archivo.name)
    try:
        with open(ruta, 'wb') as f:
            f.write(archivo.read())
        logging.info(f"Archivo guardado: {ruta}")
        return ruta
    except Exception as e:
        st.error(f"Error al guardar el archivo {archivo.name}: {e}")
        logging.error(e)
        return None

def cargar_estilos():
    try:
        with open("estilos.css") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception as e:
        logging.error("No se pudo cargar estilos.css")

def normalizar_imagen(banda):
    return cv2.normalize(banda, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

def procesar_imagen_cobre(ruta_hdr):
    try:
        img = spectral.open_image(ruta_hdr)
    except Exception as e:
        st.error("Error al abrir la imagen hiperespectral.")
        logging.error(e)
        return None, None, None
    # Se lee la banda 728 (asumiendo que la imagen la posee)
    banda = img.read_band(728)
    banda_norm = normalizar_imagen(banda)
    h, w = banda_norm.shape

    # Valores fijos predefinidos
    BG_THRESHOLD = 50       # Umbral para separar fondo de la hoja
    COPPER_THRESHOLD = 180  # Umbral para detectar cobre en la hoja

    # Se crea una imagen de salida (trinarizada) de 3 canales
    trinarizada = np.zeros((h, w, 3), dtype=np.uint8)
    # Se considera que:
    # - Los píxeles con intensidad menor a BG_THRESHOLD son fondo (negro)
    # - En la región hoja (intensidad >= BG_THRESHOLD):
    #       aquellos con intensidad >= COPPER_THRESHOLD se marcan como cobre (rojo)
    #       el resto se considera hoja normal (verde)
    leaf_mask = banda_norm >= BG_THRESHOLD
    copper_mask = (banda_norm >= COPPER_THRESHOLD) & leaf_mask
    leaf_normal_mask = leaf_mask & (~copper_mask)

    trinarizada[copper_mask] = [255, 0, 0]      # Cobre en rojo
    trinarizada[leaf_normal_mask] = [0, 255, 0]   # Hoja en verde
    # El fondo ya es negro (0,0,0)

    # Calcular el porcentaje de cobre en la hoja
    total_leaf = np.count_nonzero(leaf_mask)
    total_copper = np.count_nonzero(copper_mask)
    percent_copper = (total_copper / total_leaf * 100) if total_leaf > 0 else 0

    # Crear una imagen "normal" en escala de grises convertida a color
    normal_img = cv2.cvtColor(banda_norm, cv2.COLOR_GRAY2BGR)
    # Superponer la detección de cobre: se crea una máscara roja y se mezcla con la imagen normal
    red_mask = np.zeros_like(normal_img)
    red_mask[copper_mask] = [0, 0, 255]  # Nota: OpenCV usa BGR, por lo que rojo es (0,0,255)
    overlay = cv2.addWeighted(normal_img, 1.0, red_mask, 0.5, 0)

    return trinarizada, percent_copper, overlay

def main():
    st.title("Detección Automática de Cobre en Hojas")
    cargar_estilos()

    st.markdown("### Subir imagen hiperespectral (.bil y .bil.hdr)")
    archivos_subidos = st.file_uploader("Cargar archivos", accept_multiple_files=True, type=["bil", "bil.hdr"])
    if archivos_subidos:
        hdr_file, bil_file, nombre_base = validar_archivos_hiperespectrales(archivos_subidos)
        if hdr_file and bil_file:
            ruta_hdr = guardar_archivo(hdr_file)
            guardar_archivo(bil_file)  # Se guarda el archivo .bil aunque no se use en este procesamiento
            if st.button("PLAY"):
                with st.spinner("Procesando imagen..."):
                    trinarizada, percent_copper, overlay = procesar_imagen_cobre(ruta_hdr)
                    if trinarizada is not None:
                        st.image(trinarizada, caption="Imagen trinarizada (Fondo: negro, Hoja: verde, Cobre: rojo)", use_column_width=True)
                        st.markdown(f"**Porcentaje de cobre en la hoja:** {percent_copper:.2f}%")
                        st.image(overlay, caption="Imagen normal con detección de cobre superpuesta", use_column_width=True)

if __name__ == "__main__":
    main()