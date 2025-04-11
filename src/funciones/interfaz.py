import cv2
import streamlit as st
import spectral
import numpy as np
from funciones.archivos import guardar_archivos_subidos
from funciones.procesamiento import aplicar_procesamiento, realizar_post_procesamiento

def cargar_hyper_bin():
    st.markdown("<h2 style='text-align: center;'>Interfaz Simplificada</h2>", unsafe_allow_html=True)

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
                # Se realiza el procesamiento (trinarizado)
                img = spectral.open_image(hdr_file)
                trinarizada = aplicar_procesamiento(img)
                trinarizada = realizar_post_procesamiento(trinarizada)
                st.session_state['trinarizada'] = trinarizada

                # --- CREACIÓN DE LA IMAGEN "RGB" CON LAS BANDAS SELECCIONADAS ---
                def get_band_index(image, target_wavelength):
                    # Se extraen las longitudes de onda disponibles (centers) y se pasan a float
                    centers = np.array([float(x) for x in image.bands.centers])
                    return int(np.argmin(np.abs(centers - target_wavelength)))

                # Valores de onda aproximados para R, G, B
                wavelength_red   = 639.1  # nm
                wavelength_green = 548.4  # nm
                wavelength_blue  = 459.2  # nm

                # Localizar el índice de cada banda
                idx_r = get_band_index(img, wavelength_red)
                idx_g = get_band_index(img, wavelength_green)
                idx_b = get_band_index(img, wavelength_blue)

                # Leer cada banda
                band_r = img.read_band(idx_r)
                band_g = img.read_band(idx_g)
                band_b = img.read_band(idx_b)

                # Normalizar cada banda a [0..255]
                band_r_norm = cv2.normalize(band_r, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                band_g_norm = cv2.normalize(band_g, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                band_b_norm = cv2.normalize(band_b, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

                # Unir en formato BGR
                imagen_normal = cv2.merge([band_b_norm, band_g_norm, band_r_norm])

                # --- APLICAR HIPÓTESIS DEL MUNDO GRIS (balance de blancos sencillo) ---
                img_float = imagen_normal.astype(np.float32)
                B, G, R = cv2.split(img_float)
                avgB = np.mean(B)
                avgG = np.mean(G)
                avgR = np.mean(R)
                mean_gray = (avgB + avgG + avgR) / 3.0  # media de los 3 canales

                # Ajustar cada canal para que su media sea igual a la media global
                B *= (mean_gray / (avgB + 1e-8))
                G *= (mean_gray / (avgG + 1e-8))
                R *= (mean_gray / (avgR + 1e-8))
                img_float = cv2.merge([B, G, R])

                # Recortar valores fuera de [0..255] y convertir de nuevo a uint8
                img_balanceado = np.clip(img_float, 0, 255).astype(np.uint8)

                st.session_state['imagen_normal'] = img_balanceado

        else:
            st.error("Debes seleccionar ambos archivos (.bil y .bil.hdr).")

    # Si ya se han procesado las imágenes, se muestran en dos columnas
    if 'imagen_normal' in st.session_state and 'trinarizada' in st.session_state:
        st.markdown("<h3 style='text-align: center;'>Resultados</h3>", unsafe_allow_html=True)
        
        # Cálculo del porcentaje de recubrimiento de cobre en la hoja
        trinarizada = st.session_state['trinarizada']
        # Máscaras de hoja y cobre
        mask_hoja_verde = np.all(trinarizada == [0, 255, 0], axis=-1)
        mask_hoja_roja  = np.all(trinarizada == [255, 0, 0], axis=-1)
        area_total  = np.count_nonzero(mask_hoja_verde) + np.count_nonzero(mask_hoja_roja)
        area_cobre  = np.count_nonzero(mask_hoja_roja)
        porcentaje_cobre = (area_cobre / area_total * 100) if area_total > 0 else 0
        
        # Definir un layout más compacto: 2 columnas para imágenes con tamaño controlado
        cols = st.columns(2)
        
        # Calcular un tamaño de imagen adecuado (más pequeño que el original)
        # Ancho máximo para que quepa todo en la pantalla sin scroll
        ancho_img = 500  # Tamaño más reducido
        
        with cols[0]:
            st.image(
                st.session_state['imagen_normal'],
                caption="Imagen hiperespectral en color",
                width=ancho_img
            )
            
        with cols[1]:
            st.image(
                st.session_state['trinarizada'],
                caption="Imagen procesada (trinarizada)",
                width=ancho_img
            )
        
        # Mostrar el porcentaje de recubrimiento en una fila aparte pero con estilo destacado
        color = "red" if porcentaje_cobre > 50 else "orange" if porcentaje_cobre > 20 else "green"
        
        # Utilizamos una fila completa para mostrar el porcentaje
        st.markdown(
            f"""
            <div style="padding: 8px; border-radius: 5px; background-color: #f0f0f0; 
                      border: 2px solid {color}; text-align: center; margin-top: 10px; display: flex; align-items: center; justify-content: center;">
                <div style="font-weight: bold; font-size: 25px;color:#000000;  margin-right: 10px;">Recubrimiento de cobre:</div>
                <div style="width: 60%; height: 15px; background-color: #e0e0e0; border-radius: 3px; overflow: hidden;">
                    <div style="width: {porcentaje_cobre}%; height: 100%; background-color: {color};"></div>
                </div>
                <div style="margin-left: 10px; font-weight: bold; color:#000000; font-size: 25px;">
                    {porcentaje_cobre:.2f}%
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
