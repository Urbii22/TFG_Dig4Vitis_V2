import base64
import io
import os
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

# Valores de configuración predeterminados
st.session_state.setdefault("leaf_band", 10)
st.session_state.setdefault("leaf_threshold", 2000.0)
st.session_state.setdefault("product_band", 165)
st.session_state.setdefault(
    "product_ranges",
    [
        {"min": 3900.0, "max": 4300.0},
        {"min": 4900.0, "max": 5200.0},
    ],
)

# Rutas base
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def aplicar_tema():
    """Inyecta el CSS global y aplica variables según el tema (claro/oscuro)."""
    css_path = os.path.join(BASE_DIR, "estilos.css")
    try:
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"No se encontró el archivo de estilos en: {css_path}")

    # Inyectar variables del tema elegido
    theme = st.session_state.get("theme", "dark")
    _inject_theme_vars(theme)


def _inject_theme_vars(theme: str) -> None:
    """Sobrescribe variables CSS (:root) para el tema seleccionado.

    Args:
        theme: "light" o "dark".
    """
    if theme == "light":
        vars_css = {
            "--bg": "#FAFAFA",
            "--text": "#1A1A1A",
            "--surface": "#FFFFFF",
            "--surface-2": "#F3F3F3",
            "--border": "#E6E6E6",
            "--primary": "#B76E3A",  # cobre más sobrio para claro
            "--primary-2": "#8C4F1A",
            "--accent": "#2E7D32",
            "--accent-2": "#1B5E20",
            "--muted": "#5C5C5C",
            "--thead-bg": "#F3F3F3",
            "--hover-row": "#EFEFEF",
        }
    else:  # dark
        vars_css = {
            "--bg": "#121212",
            "--text": "#EAEAEA",
            "--surface": "#1E1E1E",
            "--surface-2": "#242424",
            "--border": "#2F2F2F",
            "--primary": "#D9895B",
            "--primary-2": "#B5651D",
            "--accent": "#66BB6A",
            "--accent-2": "#2E7D32",
            "--muted": "#B8B8B8",
            "--thead-bg": "#2F2F2F",
            "--hover-row": "#333333",
        }

    vars_block = ":root{" + "".join([f"{k}:{v};" for k, v in vars_css.items()]) + "}"
    st.markdown(f"<style>{vars_block}</style>", unsafe_allow_html=True)


def render_header(title: str = "EcoVid", subtitle: str | None = None):
    """Renderiza una cabecera compacta con logotipo y título.

    - Muestra el logotipo `recursos/EcoVid_logo.png` si está disponible.
    - Permite un subtítulo opcional para contexto.
    """
    logo_path = os.path.join(BASE_DIR, "recursos", "EcoVid_logo.png")
    logo_tag = ""
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                logo_b64 = base64.b64encode(f.read()).decode()
            logo_tag = f'<img src="data:image/png;base64,{logo_b64}" alt="EcoVid" style="width:56px;height:auto;"/>'
        except Exception:
            logo_tag = ""

    subtitle_html = (
        f'<p class="subtitle">{subtitle}</p>' if isinstance(subtitle, str) and subtitle else ""
    )

    header_html = f"""
    <header class="app-header">
      <div class="inner">
        <div class="brand">
          {logo_tag}
          <div>
            <h1>{title}</h1>
            {subtitle_html}
          </div>
        </div>
      </div>
    </header>
    """
    st.markdown(header_html, unsafe_allow_html=True)


def render_footer():
    """Muestra el pie con logotipos institucionales y créditos."""
    logos = [
        ("imagen_logo_UE.png", "logo-ue"),
        ("escudo_ubu.jpg", "logo-ubu"),
        ("gicap_logo.jpeg", "logo-gicap"),
    ]
    img_tags: list[str] = []
    for filename, css_class in logos:
        img_path = os.path.join(BASE_DIR, "recursos", filename)
        if os.path.exists(img_path):
            try:
                with open(img_path, "rb") as img_file:
                    img_b64 = base64.b64encode(img_file.read()).decode()
                mime = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
                img_tags.append(
                    f"<img src='data:{mime};base64,{img_b64}' class='{css_class}' alt='{filename}'/>"
                )
            except Exception as e:
                st.warning(f"Error al procesar el logo {filename}: {e}")
        else:
            st.warning(f"Advertencia: No se encontró el logo en la ruta esperada: {img_path}")

    footer_html = f"""
    <footer>
        {''.join(img_tags)}
        <p style='margin-top: 15px;'>© 2025 | TFG Universidad de Burgos</p>
    </footer>
    """
    st.markdown(footer_html, unsafe_allow_html=True)


def render_top_nav():
    """Barra de navegación superior con enlaces y conmutador de tema."""
    with st.container(border=False):
        cols = st.columns([1, 1, 1, 1, 1, 1, 1.2])
        with cols[0]:
            st.page_link("pages/0_Inicio.py", label="Inicio", icon="🏠")
        with cols[1]:
            st.page_link("pages/1_Procesar.py", label="Procesar", icon="🚀")
        with cols[2]:
            st.page_link("pages/2_Lotes.py", label="Lotes", icon="📦")
        with cols[3]:
            st.page_link("pages/3_Config.py", label="Config", icon="⚙️")
        with cols[4]:
            st.page_link("pages/5_Inspeccion.py", label="Inspección", icon="🔎")
        with cols[5]:
            st.page_link("pages/4_Ayuda.py", label="Ayuda", icon="❓")
        with cols[6]:
            render_theme_toggle()


def render_theme_toggle():
    """Conmutador claro/oscuro con persistencia en la sesión."""
    st.session_state.setdefault("theme", "dark")
    is_light = st.toggle("Tema claro", value=(st.session_state["theme"] == "light"))
    new_theme = "light" if is_light else "dark"
    if new_theme != st.session_state["theme"]:
        st.session_state["theme"] = new_theme


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

            raw_ranges = st.session_state.get("product_ranges", [])
            product_ranges: list[tuple[float, float]] = []
            for rng in raw_ranges:
                if isinstance(rng, dict):
                    min_val = rng.get("min")
                    max_val = rng.get("max")
                else:
                    try:
                        min_val, max_val = rng
                    except (TypeError, ValueError):
                        continue
                if min_val is None or max_val is None:
                    continue
                product_ranges.append((float(min_val), float(max_val)))

            if not product_ranges:
                st.error("Configura al menos un rango válido para la detección de producto.")
                return

            leaf_band = st.session_state.get("leaf_band")
            leaf_threshold = st.session_state.get("leaf_threshold")
            product_band = st.session_state.get("product_band")

            # Conversión a RGB y máscaras iniciales
            @st.cache_data(show_spinner=False)
            def _to_rgb_cached(hdr: str, bil: str):
                ds = envi.open(hdr, bil)
                return to_rgb(ds)

            rgb_sin = _to_rgb_cached(hdr_sin, bil_sin)
            rgb_con = _to_rgb_cached(hdr_con, bil_con)
            try:
                leaf_sin, drops_sin_raw = _obtener_mascaras(
                    cube_sin,
                    banda_hoja=leaf_band,
                    umbral_hoja=leaf_threshold,
                    banda_producto=product_band,
                    rangos_producto=product_ranges,
                )
                leaf_con, drops_con_raw = _obtener_mascaras(
                    cube_con,
                    banda_hoja=leaf_band,
                    umbral_hoja=leaf_threshold,
                    banda_producto=product_band,
                    rangos_producto=product_ranges,
                )
            except ValueError as exc:
                st.error(f"Configuración de bandas no válida: {exc}")
                return

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
                leaf_band=leaf_band,
                leaf_threshold=leaf_threshold,
                product_band=product_band,
                product_ranges=product_ranges,
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
