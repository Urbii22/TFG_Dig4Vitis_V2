import io
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from spectral.io import envi

from .archivos import guardar_archivos_subidos
from .procesamiento import to_rgb, _obtener_mascaras, trinarizar_final, aplicar_procesamiento_dual
from .alignment import _remove_petiole

# Inicializar session_state si no existe
if "processed" not in st.session_state:
    st.session_state.processed = False


def mostrar_subida_archivos():
    """Muestra los componentes para subir archivos y el botón de procesar."""
    st.markdown("#### 1. Carga de Imágenes Hiperespectrales")

    col1, col2 = st.columns(2)
    with col1:
        archivos_sin = st.file_uploader(
            "Imagen de referencia **SIN** tratamiento (.bil + .hdr)",
            type=["bil", "hdr"],
            accept_multiple_files=True,
            key="sin_gotas",
        )
    with col2:
        archivos_con = st.file_uploader(
            "Imagen **CON** tratamiento (.bil + .hdr)",
            type=["bil", "hdr"],
            accept_multiple_files=True,
            key="con_gotas",
        )

    if st.button("🚀 Iniciar Procesamiento", use_container_width=True):
        with st.spinner("Analizando imágenes... Por favor, espere."):
            hdr_sin, bil_sin, _ = guardar_archivos_subidos(archivos_sin, "sin_")
            hdr_con, bil_con, _ = guardar_archivos_subidos(archivos_con, "con_")

            if not (hdr_sin and bil_sin and hdr_con and bil_con):
                st.error("Error: Asegúrate de subir los archivos .hdr y .bil para ambas imágenes.")
                return

            # Abrir cubos hiperespectrales y procesar
            cube_sin = envi.open(hdr_sin, bil_sin)
            cube_con = envi.open(hdr_con, bil_con)

            # Conversión a RGB y máscaras iniciales
            rgb_sin = to_rgb(cube_sin)
            rgb_con = to_rgb(cube_con)
            leaf_sin, drops_sin_raw = _obtener_mascaras(cube_sin)
            leaf_con, drops_con_raw = _obtener_mascaras(cube_con)
            trin_sin = trinarizar_final(leaf_sin, drops_sin_raw & leaf_sin, np.zeros_like(leaf_sin))
            trin_con = trinarizar_final(leaf_con, drops_con_raw & leaf_con, np.zeros_like(leaf_con))

            # Procesamiento dual completo
            resultado, leaf_con_crop, leaf_sin_aligned, common_shape, hoja_comun, gotas_final = aplicar_procesamiento_dual(cube_con, cube_sin)

            # Guardar todo en session_state
            st.session_state.update({
                "processed": True, "rgb_sin": rgb_sin, "rgb_con": rgb_con,
                "trin_sin": trin_sin, "trin_con": trin_con,
                "resultado_final": resultado, "leaf_con_crop": leaf_con_crop,
                "leaf_sin_aligned": leaf_sin_aligned, "common_shape": common_shape,
                "hoja_comun": hoja_comun, "gotas_final": gotas_final
            })
            st.success("¡Procesamiento completado con éxito!")


def mostrar_previsualizacion_y_resultados():
    """Muestra las previsualizaciones y los resultados del análisis."""
    st.markdown("---")
    st.markdown("#### 2. Resultados del Análisis")

    # Recuperar datos de la sesión
    resultado_final = st.session_state.resultado_final
    hoja_comun = st.session_state.hoja_comun
    gotas_final = st.session_state.gotas_final

    # Calcular métricas
    num_pixeles_hoja_comun = np.count_nonzero(hoja_comun)
    num_pixeles_gotas_final = np.count_nonzero(gotas_final)
    porcentaje = (num_pixeles_gotas_final / num_pixeles_hoja_comun * 100) if num_pixeles_hoja_comun > 0 else 0.0

    # --- Presentación de resultados ---
    col_res1, col_res2 = st.columns([1, 1])

    with col_res1:
        st.markdown("##### Detección de Producto")
        st.image(resultado_final, caption="Resultado: Hoja (verde), Producto detectado (rojo)", width=750)

    with col_res2:
        st.metric(label="Porcentaje de Recubrimiento", value=f"{porcentaje:.2f}%")
        st.markdown("El recubrimiento se calcula como el porcentaje de píxeles con producto detectado sobre el total de píxeles de la hoja común.")

        # Botón de descarga para la imagen final
        buf = io.BytesIO()
        Image.fromarray(resultado_final).save(buf, format="PNG")

        if st.download_button(
            label="📥 Descargar Imagen de Resultado",
            data=buf.getvalue(),
            file_name="resultado_EcoVid.png",
            mime="image/png",
            use_container_width=True
        ):
            st.toast('¡Descarga iniciada!', icon='✅')

    # --- Expander para visualizaciones avanzadas y descargas adicionales ---
    with st.expander("Ver detalles y descargas adicionales"):
        st.markdown("##### Visualización del Alineamiento")

        leaf_con_viz = st.session_state.leaf_con_crop
        leaf_sin_viz = st.session_state.leaf_sin_aligned

        h, w = st.session_state.common_shape
        overlay_viz = np.zeros((h, w, 3), dtype=np.uint8)

        overlay_viz[leaf_con_viz] = [0, 255, 0]
        overlay_viz[leaf_sin_viz] = [255, 0, 0]

        st.image(overlay_viz, caption="Superposición Alineación (Verde: CON, Rojo: SIN alineada a CON)", width=450)
        st.markdown("---")

        TARGET_SIZE = (550, 800)

        rgb_con_resized = cv2.resize(st.session_state.rgb_con, TARGET_SIZE, interpolation=cv2.INTER_AREA)
        trin_con_resized = cv2.resize(st.session_state.trin_con, TARGET_SIZE, interpolation=cv2.INTER_NEAREST)

        rgb_sin_resized = cv2.resize(st.session_state.rgb_sin, TARGET_SIZE, interpolation=cv2.INTER_AREA)
        trin_sin_resized = cv2.resize(st.session_state.trin_sin, TARGET_SIZE, interpolation=cv2.INTER_NEAREST)

        col_details1, col_details2 = st.columns(2)

        with col_details1:
            st.markdown("##### Imagen CON tratamiento")
            st.image(rgb_con_resized, caption="RGB CON Tratamiento")
            st.image(trin_con_resized, caption="Trinarizada CON Tratamiento")

        with col_details2:
            st.markdown("##### Imagen SIN tratamiento")
            st.image(rgb_sin_resized, caption="RGB SIN Tratamiento")
            st.image(trin_sin_resized, caption="Trinarizada SIN Tratamiento")

        st.markdown("---")
        st.markdown("##### Descargar Trinarizadas Base")
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            buf_con = io.BytesIO()
            Image.fromarray(st.session_state.trin_con).save(buf_con, format="PNG")
            if st.download_button("📥 Descargar Trinarizada CON", data=buf_con.getvalue(), file_name="trin_con.png", mime="image/png", use_container_width=True):
                st.toast('Descarga de "Trin. CON" iniciada.', icon='✅')

        with col_dl2:
            buf_sin = io.BytesIO()
            Image.fromarray(st.session_state.trin_sin).save(buf_sin, format="PNG")
            if st.download_button("📥 Descargar Trinarizada SIN", data=buf_sin.getvalue(), file_name="trin_sin.png", mime="image/png", use_container_width=True):
                st.toast('Descarga de "Trin. SIN" iniciada.', icon='✅')

