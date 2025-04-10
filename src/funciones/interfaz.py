import cv2
import streamlit as st
import spectral
import numpy as np
from funciones.archivos import guardar_archivos_subidos
from funciones.procesamiento import aplicar_procesamiento, realizar_post_procesamiento

def cargar_hyper_bin():
    # st.markdown("<h2 style='text-align: center;'>Interfaz Simplificada</h2>", unsafe_allow_html=True)

    # Mostrar dos columnas para los dos botones: uno para seleccionar la imagen y otro para procesarla
    col_botones = st.columns(2)
    with col_botones[0]:
        # Botón de selección de imagen (file uploader)
        archivos_subidos = st.file_uploader(
            "Seleccionar imagen",
            accept_multiple_files=True,
            type=["bil", "bil.hdr"]
        )
    with col_botones[1]:
        # Botón para procesar la imagen
        procesar = st.button("Procesar imagen", help="Procesa la imagen hiperespectral")

    # Al pulsar "Procesar imagen", se valida que se hayan seleccionado ambos archivos (.bil y .bil.hdr)
    if procesar:
        if archivos_subidos and len(archivos_subidos) == 2:
            hdr_file, bil_file, nombre_hyper = guardar_archivos_subidos(archivos_subidos)
            if hdr_file and bil_file:
                # Se utiliza un método fijo ("Fijo") para el procesamiento
                img = spectral.open_image(hdr_file)
                trinarizada = aplicar_procesamiento(img, "Fijo")
                trinarizada = realizar_post_procesamiento(trinarizada)
                st.session_state['trinarizada'] = trinarizada

                # Obtener imagen RGB (hoja) utilizando la banda 164
                banda_hoja = img.read_band(164)
                banda_hoja_norm = cv2.normalize(banda_hoja, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                imagen_normal = cv2.cvtColor(banda_hoja_norm, cv2.COLOR_GRAY2BGR)
                st.session_state['imagen_normal'] = imagen_normal
        else:
            st.error("Debes seleccionar ambos archivos (.bil y .bil.hdr).")

    # Si ya se han procesado las imágenes, se muestran en dos columnas (sin scroll)
    if 'imagen_normal' in st.session_state and 'trinarizada' in st.session_state:
        st.markdown("<h3 style='text-align: center;'>Resultados</h3>", unsafe_allow_html=True)
        cols = st.columns(2)
        with cols[0]:
            st.image(
                st.session_state['imagen_normal'],
                caption="Imagen RGB (hoja)",
                use_column_width=True
            )
        with cols[1]:
            st.image(
                st.session_state['trinarizada'],
                caption="Imagen procesada (trinarizada)",
                use_column_width=True
            )
