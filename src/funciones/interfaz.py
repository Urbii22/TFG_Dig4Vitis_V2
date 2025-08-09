import io
import time

import cv2
import numpy as np
import streamlit as st
from PIL import Image
from spectral.io import envi

from .archivos import guardar_archivos_subidos
from .procesamiento import _obtener_mascaras, aplicar_procesamiento_dual, to_rgb, trinarizar_final

# Inicializar session_state si no existe
if "processed" not in st.session_state:
    st.session_state.processed = False


@st.cache_resource(show_spinner=False)
def _abrir_cubos(hdr_sin: str, bil_sin: str, hdr_con: str, bil_con: str):
    return envi.open(hdr_sin, bil_sin), envi.open(hdr_con, bil_con)


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
            hdr_sin, bil_sin, nombre_base_sin = guardar_archivos_subidos(archivos_sin, "sin_")
            hdr_con, bil_con, nombre_base_con = guardar_archivos_subidos(archivos_con, "con_")

            if not (hdr_sin and bil_sin and hdr_con and bil_con):
                st.error("Error: Asegúrate de subir los archivos .hdr y .bil para ambas imágenes.")
                return

            # Verificación de que los identificadores de muestra de los archivos coinciden
            if nombre_base_sin != nombre_base_con:
                st.error(
                    "Error: Los identificadores de muestra en los nombres de archivo no coinciden. "
                    "Asegúrate de que ambas imágenes ('CON' y 'SIN' tratamiento) pertenecen a la misma muestra."
                    f"\n- Identificador SIN tratamiento: **{nombre_base_sin}**"
                    f"\n- Identificador CON tratamiento: **{nombre_base_con}**"
                )
                return

            # Validación temprana de archivos y apertura cacheada
            import os

            for p in (hdr_sin, bil_sin, hdr_con, bil_con):
                if not os.path.exists(p):
                    st.error(f"Fichero no encontrado: {p}")
                    return
            for p in (hdr_sin, hdr_con):
                if not p.lower().endswith(".hdr"):
                    st.error(f"Metadatos no válidos (se esperaba .hdr): {p}")
                    return
            for p in (bil_sin, bil_con):
                if not p.lower().endswith(".bil"):
                    st.error(f"Datos no válidos (se esperaba .bil): {p}")
                    return

            # Abrir cubos hiperespectrales y procesar (cacheado)
            cube_sin, cube_con = _abrir_cubos(hdr_sin, bil_sin, hdr_con, bil_con)

            # Conversión a RGB y máscaras iniciales
            @st.cache_data(show_spinner=False)
            def _to_rgb_cached(hdr: str, bil: str):
                ds = envi.open(hdr, bil)
                return to_rgb(ds)

            rgb_sin = _to_rgb_cached(hdr_sin, bil_sin)
            rgb_con = _to_rgb_cached(hdr_con, bil_con)
            leaf_sin, drops_sin_raw = _obtener_mascaras(cube_sin)
            leaf_con, drops_con_raw = _obtener_mascaras(cube_con)
            trin_sin = trinarizar_final(leaf_sin, drops_sin_raw & leaf_sin, np.zeros_like(leaf_sin))
            trin_con = trinarizar_final(leaf_con, drops_con_raw & leaf_con, np.zeros_like(leaf_con))

            # Procesamiento dual completo con métricas y tiempo
            t0 = time.perf_counter()
            (
                resultado,
                leaf_con_crop,
                leaf_sin_aligned,
                common_shape,
                hoja_comun,
                gotas_final,
                align_metrics,
            ) = aplicar_procesamiento_dual(
                cube_con,
                cube_sin,
                orb_nfeatures=st.session_state.get("orb_nfeatures"),
                detection_scale_factor=st.session_state.get("detection_scale_factor"),
                ransac_reproj_thresh=st.session_state.get("ransac_reproj_thresh"),
                ransac_max_iters=st.session_state.get("ransac_max_iters"),
                ransac_confidence=st.session_state.get("ransac_confidence"),
            )
            total_time_s = time.perf_counter() - t0

            # Guardar todo en session_state
            st.session_state.update(
                {
                    "processed": True,
                    "rgb_sin": rgb_sin,
                    "rgb_con": rgb_con,
                    "trin_sin": trin_sin,
                    "trin_con": trin_con,
                    "resultado_final": resultado,
                    "leaf_con_crop": leaf_con_crop,
                    "leaf_sin_aligned": leaf_sin_aligned,
                    "common_shape": common_shape,
                    "hoja_comun": hoja_comun,
                    "gotas_final": gotas_final,
                    "align_metrics": align_metrics,
                    "total_time_s": total_time_s,
                    # Rutas para inspección posterior
                    "hdr_sin_path": hdr_sin,
                    "bil_sin_path": bil_sin,
                    "hdr_con_path": hdr_con,
                    "bil_con_path": bil_con,
                }
            )
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
    porcentaje = (
        (num_pixeles_gotas_final / num_pixeles_hoja_comun * 100)
        if num_pixeles_hoja_comun > 0
        else 0.0
    )
    align_metrics = st.session_state.get("align_metrics", {})
    total_time_s = st.session_state.get("total_time_s", None)

    # --- Presentación de resultados ---
    col_res1, col_res2 = st.columns([1, 1])

    with col_res1:
        st.markdown("##### Detección de Producto")
        st.image(
            resultado_final, caption="Resultado: Hoja (verde), Producto detectado (rojo)", width=750
        )

    with col_res2:
        st.metric(label="Porcentaje de Recubrimiento", value=f"{porcentaje:.2f}%")
        # Panel de métricas de alineación y tiempo
        with st.container(border=True):
            st.markdown("##### Métricas del Proceso")
            cols = st.columns(2)
            with cols[0]:
                st.metric("Matches totales", f"{align_metrics.get('n_matches', '—')}")
                st.metric("Inliers", f"{align_metrics.get('n_inliers', '—')}")
            with cols[1]:
                inlier_ratio = align_metrics.get("inlier_ratio")
                st.metric(
                    "Ratio inliers",
                    f"{inlier_ratio*100:.1f}%" if isinstance(inlier_ratio, (float | int)) else "—",
                )
                err = align_metrics.get("mean_reproj_error_px")
                st.metric(
                    "Error reproy. (px)", f"{err:.2f}" if isinstance(err, (float | int)) else "—"
                )
            if total_time_s is not None:
                st.metric("Tiempo total", f"{total_time_s:.2f} s")
        st.markdown(
            "El recubrimiento se calcula como el porcentaje de píxeles con producto detectado sobre el total de píxeles de la hoja común."
        )

        # Botón de descarga para la imagen final
        buf = io.BytesIO()
        Image.fromarray(resultado_final).save(buf, format="PNG")

        if st.download_button(
            label="📥 Descargar Imagen de Resultado",
            data=buf.getvalue(),
            file_name="resultado_EcoVid.png",
            mime="image/png",
            use_container_width=True,
        ):
            st.toast("¡Descarga iniciada!", icon="✅")

    # --- Expander para visualizaciones avanzadas y descargas adicionales ---
    with st.expander("Ver detalles y descargas adicionales"):
        st.markdown("##### Visualización del Alineamiento")

        leaf_con_viz = st.session_state.leaf_con_crop
        leaf_sin_viz = st.session_state.leaf_sin_aligned

        h, w = st.session_state.common_shape
        overlay_viz = np.zeros((h, w, 3), dtype=np.uint8)

        overlay_viz[leaf_con_viz] = [0, 255, 0]
        overlay_viz[leaf_sin_viz] = [255, 0, 0]

        st.image(
            overlay_viz,
            caption="Superposición Alineación (Verde: CON, Rojo: SIN alineada a CON)",
            width=450,
        )
        st.markdown("---")
        # Comparador simple (antes/después) con slider de opacidad
        st.markdown("##### Comparador Antes/Después (opacidad)")
        alpha = st.slider("Opacidad de la trinarizada CON", 0.0, 1.0, 0.6, 0.05)
        base = st.session_state.rgb_con.copy().astype(np.float32)
        overlay = st.session_state.trin_con.copy().astype(np.float32)
        blend = (alpha * overlay + (1 - alpha) * base).clip(0, 255).astype(np.uint8)
        st.image(blend, caption="Comparación opaca sobre RGB CON")

        TARGET_SIZE = (550, 800)

        rgb_con_resized = cv2.resize(
            st.session_state.rgb_con, TARGET_SIZE, interpolation=cv2.INTER_AREA
        )
        trin_con_resized = cv2.resize(
            st.session_state.trin_con, TARGET_SIZE, interpolation=cv2.INTER_NEAREST
        )

        rgb_sin_resized = cv2.resize(
            st.session_state.rgb_sin, TARGET_SIZE, interpolation=cv2.INTER_AREA
        )
        trin_sin_resized = cv2.resize(
            st.session_state.trin_sin, TARGET_SIZE, interpolation=cv2.INTER_NEAREST
        )

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
            if st.download_button(
                "📥 Descargar Trinarizada CON",
                data=buf_con.getvalue(),
                file_name="trin_con.png",
                mime="image/png",
                use_container_width=True,
            ):
                st.toast('Descarga de "Trin. CON" iniciada.', icon="✅")

        with col_dl2:
            buf_sin = io.BytesIO()
            Image.fromarray(st.session_state.trin_sin).save(buf_sin, format="PNG")
            if st.download_button(
                "📥 Descargar Trinarizada SIN",
                data=buf_sin.getvalue(),
                file_name="trin_sin.png",
                mime="image/png",
                use_container_width=True,
            ):
                st.toast('Descarga de "Trin. SIN" iniciada.', icon="✅")
