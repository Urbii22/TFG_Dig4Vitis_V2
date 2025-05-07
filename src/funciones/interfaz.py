"""
Interfaz Streamlit.
Solo se ocupa de:
  • Cargar archivos subidos por el usuario.
  • Mostrar imágenes, sliders y botones.
  • Invocar a las rutinas de procesamiento.
"""

import io
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from spectral.io import envi

from funciones.archivos import guardar_archivos_subidos
from funciones.procesamiento import (
    aplicar_procesamiento,
    _obtener_mascaras,
    to_rgb,
    matriz_transformacion,
    warp_mask,
    trinarizar_final,
)

# -------------------------------------------------------------------
# Página principal
# -------------------------------------------------------------------
def cargar_hyper_bin():
    st.markdown("### 1. Selecciona las imágenes hiperespectrales")

    col1, col2 = st.columns(2)
    with col1:
        archivos_sin = st.file_uploader(
            "Imagen **SIN** gotas (.bil + .bil.hdr)",
            type=["bil", "bil.hdr"],
            accept_multiple_files=True,
            key="sin_gotas",
        )
    with col2:
        archivos_con = st.file_uploader(
            "Imagen **CON** gotas (.bil + .bil.hdr)",
            type=["bil", "bil.hdr"],
            accept_multiple_files=True,
            key="con_gotas",
        )

    # -----------------------------------------------------------------
    # Procesamiento inicial
    # -----------------------------------------------------------------
    if st.button("Procesar imágenes"):
        if not (archivos_sin and len(archivos_sin) == 2):
            st.error("Faltan archivos en la imagen **SIN gotas**.")
            return
        if not (archivos_con and len(archivos_con) == 2):
            st.error("Faltan archivos en la imagen **CON gotas**.")
            return

        hdr_sin, bil_sin, _ = guardar_archivos_subidos(archivos_sin, prefijo="sin_")
        hdr_con, bil_con, _ = guardar_archivos_subidos(archivos_con, prefijo="con_")
        if None in (hdr_sin, bil_sin, hdr_con, bil_con):
            st.error("Debes subir .bil y .bil.hdr para ambas imágenes.")
            return

        img_sin = envi.open(hdr_sin, bil_sin)
        img_con = envi.open(hdr_con, bil_con)

        # Trinarizados base (solo informativos)
        trin_sin = aplicar_procesamiento(img_sin)
        trin_con = aplicar_procesamiento(img_con)

        # Máscaras
        leaf_sin_raw, drops_sin_raw = _obtener_mascaras(img_sin)
        leaf_con_raw, drops_con_raw = _obtener_mascaras(img_con)
        drop_sin = drops_sin_raw & leaf_sin_raw
        drop_con = drops_con_raw & leaf_con_raw

        # RGB pseudo-color
        rgb_sin = to_rgb(img_sin)
        rgb_con = to_rgb(img_con)

        # Recorte a área común
        h = min(
            leaf_sin_raw.shape[0],
            leaf_con_raw.shape[0],
            trin_sin.shape[0],
            trin_con.shape[0],
        )
        w = min(
            leaf_sin_raw.shape[1],
            leaf_con_raw.shape[1],
            trin_sin.shape[1],
            trin_con.shape[1],
        )

        leaf_sin = leaf_sin_raw[:h, :w]
        leaf_con = leaf_con_raw[:h, :w]
        drop_sin = drop_sin[:h, :w]
        drop_con = drop_con[:h, :w]
        rgb_sin  = rgb_sin[:h, :w]
        rgb_con  = rgb_con[:h, :w]
        trin_sin = trin_sin[:h, :w]
        trin_con = trin_con[:h, :w]

        # Guardar en sesión (sin R0 y t0 iniciales)
        st.session_state.update(
            {
                "rgb_sin": rgb_sin,
                "trin_sin": trin_sin,
                "rgb_con": rgb_con,
                "trin_con": trin_con,
                "leaf_sin": leaf_sin,
                "leaf_con": leaf_con,
                "drop_con": drop_con,
                "drop_sin": drop_sin,
                "size": (h, w),
                "processed": True, # Añadir flag para saber si se procesó
            }
        )

    # -----------------------------------------------------------------
    # Controles y resultados
    # -----------------------------------------------------------------
    if st.session_state.get("processed", False): # Usar el flag
        st.markdown("## Resultados")

        # Vista previa de imágenes
        st.markdown("#### SIN gotas")
        c1, c2 = st.columns(2)
        c1.image(st.session_state["rgb_sin"],  caption="RGB SIN",  width=350)
        c2.image(st.session_state["trin_sin"], caption="Trinarizada SIN", width=350)

        st.markdown("#### CON gotas")
        c3, c4 = st.columns(2)
        c3.image(st.session_state["rgb_con"],  caption="RGB CON",  width=350)
        c4.image(st.session_state["trin_con"], caption="Trinarizada CON", width=350)

        # Controles de ajuste
        ov_col, ctl_col = st.columns([3, 1])
        ctl_col.markdown("### Ajuste manual")

        scale_adj = ctl_col.slider("Escala", 0.5, 2.0, 1.0, 0.01) # Renombrado
        rot_adj   = ctl_col.slider("Rotación (º)", -180, 180, 0, 1) # Renombrado
        dx        = ctl_col.slider("Desplaz. X (px)", -800, 800, 0, 1)
        dy        = ctl_col.slider("Desplaz. Y (px)", -800, 800, 0, 1)

        # Reconstruimos la transformación definitiva desde cero
        h, w = st.session_state["size"]
        # Inicializar R0 (identidad) y t0 (ceros) como base neutra
        R0_base = np.array([[1.0, 0.0], [0.0, 1.0]])
        t0_base = np.array([0.0, 0.0])

        M = matriz_transformacion(
            R0_base, # Usar base neutra
            t0_base, # Usar base neutra
            scale_adj,
            rot_adj,
            dx,
            dy,
        )

        # Warp de la máscara de hoja SIN
        warped_leaf_sin = warp_mask(st.session_state["leaf_sin"], M, (h, w))

        # Superposición de las dos máscaras de hoja
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        canvas[st.session_state["leaf_con"]] = [0, 255, 0]     # verde = hoja CON
        canvas[warped_leaf_sin]            = [0,   0, 255]    # azul  = hoja SIN alineada

        ov_col.markdown("### Máscara sólida de ajuste")
        ov_col.image(
            canvas,
            caption="Verde = hoja CON, Azul = hoja SIN alineada",
            width=350,
        )

        # -------------------------------------------------------------
        # Trinarizada final y descargas
        # -------------------------------------------------------------
        if ov_col.button("Aplicar resta de gotas alineadas"):
            trinarizada_final = trinarizar_final(
                st.session_state["leaf_con"],
                st.session_state["drop_con"],
                warp_mask(st.session_state["drop_sin"], M, (h, w)),
            )

            ov_col.markdown("### Trinarizada final (ruido reducido)")
            ov_col.image(
                trinarizada_final,
                caption="Verde = hoja, Rojo = gotas únicas (>5 px)",
                width=350,
            )



            # ----- Cálculo del porcentaje de recubrimiento de gotas -----
            num_pixeles_hoja = np.count_nonzero(st.session_state["leaf_con"])
            num_pixeles_gotas = np.count_nonzero(
                (trinarizada_final == [255, 0, 0]).all(axis=-1)
            )
            porcentaje_cobre = (
                round(num_pixeles_gotas / num_pixeles_hoja * 100, 2)
                if num_pixeles_hoja
                else 0
            )

            # Mostrar el porcentaje de recubrimiento en una fila aparte pero con estilo destacado
            color = "red" if porcentaje_cobre < 20 else "orange" if porcentaje_cobre < 50 else "green"

            ov_col.markdown(
                f"""
                <div style="padding: 8px; border-radius: 5px; background-color: #f0f0f0;
                            border: 2px solid {color}; text-align: center; margin-top: 10px;
                            display: flex; align-items: center; justify-content: center;">
                    <div style="font-weight: bold; font-size: 25px; color: #000000; margin-right: 10px;">
                        Recubrimiento de cobre:
                    </div>
                    <div style="width: 60%; height: 15px; background-color: #e0e0e0;
                                border-radius: 3px; overflow: hidden;">
                        <div style="width: {porcentaje_cobre}%; height: 100%; background-color: {color};"></div>
                    </div>
                    <div style="margin-left: 10px; font-weight: bold; color: #000000; font-size: 25px;">
                        {porcentaje_cobre:.2f}%
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Descarga de la trinarizada final
            buf = io.BytesIO()
            Image.fromarray(trinarizada_final).save(buf, format="PNG")
            buf.seek(0)
            ov_col.download_button(
                label="Descargar trinarizada final",
                data=buf,
                file_name="trinarizada_final.png",
                mime="image/png",
            )

            # Descarga de trinarizadas base
            for nombre, clave in [
                ("con_gotas", "trin_con"),
                ("sin_gotas", "trin_sin"),
            ]:
                buf_tmp = io.BytesIO()
                Image.fromarray(st.session_state[clave]).save(buf_tmp, format="PNG")
                buf_tmp.seek(0)
                ov_col.download_button(
                    f"Descargar trinarizada {nombre}",
                    data=buf_tmp,
                    file_name=f"trinarizada_{nombre}.png",
                    mime="image/png",
                )
