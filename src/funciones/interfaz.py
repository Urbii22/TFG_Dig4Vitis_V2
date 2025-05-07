"""
Interfaz Streamlit.
Carga, muestra y aplica alineación + trinarización automática usando las funciones del módulo de procesamiento.
"""

import io
import numpy as np
import streamlit as st
from PIL import Image
from spectral.io import envi

from funciones.archivos import guardar_archivos_subidos
from funciones.procesamiento import (
    to_rgb,
    _obtener_mascaras,
    trinarizar_final,
    aplicar_procesamiento_dual,
)


def cargar_hyper_bin():
    st.markdown("### 1. Selecciona las imágenes hiperespectrales")

    col1, col2 = st.columns(2)
    with col1:
        archivos_sin = st.file_uploader(
            "Imagen **SIN** gotas (.bil + .hdr)",
            type=["bil", "hdr"],
            accept_multiple_files=True,
            key="sin_gotas",
        )
    with col2:
        archivos_con = st.file_uploader(
            "Imagen **CON** gotas (.bil + .hdr)",
            type=["bil", "hdr"],
            accept_multiple_files=True,
            key="con_gotas",
        )

    if st.button("Procesar imágenes"):
        hdr_sin, bil_sin, _ = guardar_archivos_subidos(archivos_sin)
        hdr_con, bil_con, _ = guardar_archivos_subidos(archivos_con)
        if hdr_sin is None or bil_sin is None:
            st.error("Debes subir `.hdr` y `.bil` de la imagen **SIN** gotas.")
            return
        if hdr_con is None or bil_con is None:
            st.error("Debes subir `.hdr` y `.bil` de la imagen **CON** gotas.")
            return

        # Abrir cubos hiperespectrales
        cube_sin = envi.open(hdr_sin, bil_sin)
        cube_con = envi.open(hdr_con, bil_con)

        # Conversión a RGB para previsualizar
        rgb_sin = to_rgb(cube_sin)
        rgb_con = to_rgb(cube_con)

        # Máscaras crudas
        leaf_sin, drops_sin_raw = _obtener_mascaras(cube_sin)
        leaf_con, drops_con_raw = _obtener_mascaras(cube_con)
        drops_sin = drops_sin_raw & leaf_sin
        drops_con = drops_con_raw & leaf_con

        # Trinarizaciones básicas
        trin_sin = trinarizar_final(leaf_sin, drops_sin, np.zeros_like(drops_sin))
        trin_con = trinarizar_final(leaf_con, drops_con, np.zeros_like(drops_con))

        # Guardar datos en sesión
        st.session_state.update({
            "processed": True,
            "cube_sin": cube_sin,
            "cube_con": cube_con,
            "rgb_sin": rgb_sin,
            "rgb_con": rgb_con,
            "trin_sin": trin_sin,
            "trin_con": trin_con,
        })

    if not st.session_state.get("processed", False):
        return

    # Recuperar variables de sesión
    cube_sin = st.session_state["cube_sin"]
    cube_con = st.session_state["cube_con"]
    rgb_sin = st.session_state["rgb_sin"]
    rgb_con = st.session_state["rgb_con"]
    trin_sin = st.session_state["trin_sin"]
    trin_con = st.session_state["trin_con"]

    # 2. Previsualización
    st.markdown("### 2. Previsualización")
    colA, colB = st.columns(2)
    colA.image(rgb_sin, caption="RGB SIN gotas", width=300)
    colB.image(rgb_con, caption="RGB CON gotas", width=300)
    colA.image(trin_sin, caption="Trinarizada SIN", width=300)
    colB.image(trin_con, caption="Trinarizada CON", width=300)

    # 3. Alineación automática + trinarización final
    st.markdown("---")
    st.markdown("### 3. Alineación automática + trinarización final")
    if st.button("Ejecutar alineación automática"):
        # Aplicar procesamiento dual completo
        # Ahora devuelve: resultado_trinarizado, leaf_con_recortada, leaf_sin_alineada, forma_comun
        resultado_trinarizado, leaf_con_crop, leaf_sin_aligned, common_shape = aplicar_procesamiento_dual(cube_con, cube_sin)

        # Crear visualización de superposición
        h, w = common_shape
        overlay_viz = np.zeros((h, w, 3), dtype=np.uint8)
        overlay_viz[leaf_con_crop] = [0, 255, 0]  # Hoja CON en Verde
        # Superponer hoja SIN alineada en Rojo para ver diferencias/coincidencias
        # Crear una máscara temporal para la superposición sin modificar leaf_con_crop en overlay_viz
        temp_sin_mask_viz = np.zeros_like(overlay_viz)
        temp_sin_mask_viz[leaf_sin_aligned] = [255, 0, 0] # Hoja SIN alineada en Rojo
        
        # Combinar: donde ambas hojas están, podría mostrarse un color mixto o priorizar una.
        # Aquí, simplemente superponemos, el rojo sobreescribirá el verde si hay solapamiento.
        # Para una mejor visualización de solapamiento, podríamos hacer:
        # overlay_viz[leaf_con_crop & leaf_sin_aligned] = [255, 255, 0] # Amarillo para solapamiento
        # overlay_viz[leaf_con_crop & ~leaf_sin_aligned] = [0, 255, 0] # Verde solo CON
        # overlay_viz[~leaf_con_crop & leaf_sin_aligned] = [255, 0, 0] # Rojo solo SIN
        # Por simplicidad, mantenemos la superposición directa:
        overlay_viz[leaf_sin_aligned] = [255, 0, 0] # Hoja SIN alineada en Rojo sobreescribe/se añade

        st.image(overlay_viz, caption="Superposición Alineación (Verde: CON, Rojo: SIN alineada a CON)", width=300)
        st.image(resultado_trinarizado, caption="Trinarizada Automática", width=300)

        # Calcular y mostrar porcentaje de recubrimiento
        num_pixeles_hoja = np.count_nonzero(np.all(resultado_trinarizado == [0, 255, 0], axis=-1))
        num_pixeles_producto = np.count_nonzero(np.all(resultado_trinarizado == [255, 0, 0], axis=-1))

        porcentaje_recubrimiento = 0
        if num_pixeles_hoja > 0:
            porcentaje_recubrimiento = (num_pixeles_producto / num_pixeles_hoja) * 100
        
        st.metric(label="Recubrimiento de Producto en Hoja", value=f"{porcentaje_recubrimiento:.2f}%")

        # Botón de descarga
        buf = io.BytesIO()
        Image.fromarray(resultado_trinarizado).save(buf, format="PNG")
        buf.seek(0)
        st.download_button(
            "Descargar trinarizada automática",
            data=buf,
            file_name="trinarizada_automatica.png",
            mime="image/png",
        )

    # 4. Descarga de trinarizadas base
    st.markdown("---")
    st.markdown("### 4. Descarga de trinarizadas base")
    for tag, arr in [("sin", trin_sin), ("con", trin_con)]:
        buf = io.BytesIO()
        Image.fromarray(arr).save(buf, format="PNG")
        buf.seek(0)
        st.download_button(
            f"Descargar {tag}",
            data=buf,
            file_name=f"trinarizada_{tag}.png",
            mime="image/png",
        )
