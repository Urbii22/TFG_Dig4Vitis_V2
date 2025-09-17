import streamlit as st

from funciones.interfaz import aplicar_tema, render_header, render_top_nav

st.set_page_config(page_title="EcoVid – Configuración", layout="wide")

aplicar_tema()
render_header(title="EcoVid", subtitle="Configuración")
render_top_nav()

st.markdown("---")
st.write("Parámetros aplicados al pipeline de alineación y detección en próximas ejecuciones.")

st.session_state.setdefault("orb_nfeatures", 4000)
st.session_state.setdefault("detection_scale_factor", 0.75)
st.session_state.setdefault("ransac_reproj_thresh", 3.0)
st.session_state.setdefault("ransac_max_iters", 5000)
st.session_state.setdefault("ransac_confidence", 0.995)
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

normalized_ranges: list[dict[str, float]] = []
for _rng in st.session_state.get("product_ranges", []):
    if isinstance(_rng, dict):
        min_val = _rng.get("min")
        max_val = _rng.get("max")
    else:
        try:
            min_val, max_val = _rng
        except (TypeError, ValueError):
            continue
    if min_val is None or max_val is None:
        continue
    normalized_ranges.append({"min": float(min_val), "max": float(max_val)})
if normalized_ranges:
    st.session_state["product_ranges"] = normalized_ranges

st.number_input("ORB nfeatures", min_value=500, max_value=20000, step=500, key="orb_nfeatures")
st.slider(
    "Factor de escala para detección",
    min_value=0.25,
    max_value=1.0,
    step=0.05,
    key="detection_scale_factor",
)
st.slider(
    "RANSAC reproj. thresh", min_value=0.5, max_value=10.0, step=0.5, key="ransac_reproj_thresh"
)
st.number_input(
    "RANSAC max iters", min_value=1000, max_value=20000, step=1000, key="ransac_max_iters"
)
st.slider("RANSAC confidence", min_value=0.80, max_value=0.999, step=0.001, key="ransac_confidence")


st.markdown("---")
st.markdown("#### Ajustes de bandas y binarización")
col_leaf_band, col_leaf_thresh = st.columns(2)
with col_leaf_band:
    st.number_input(
        "Banda (1-indexada) para segmentar la hoja",
        min_value=1,
        max_value=5000,
        step=1,
        key="leaf_band",
    )
with col_leaf_thresh:
    st.number_input(
        "Umbral para la banda de la hoja",
        min_value=0.0,
        max_value=100000.0,
        step=50.0,
        key="leaf_threshold",
    )
st.number_input(
    "Banda (1-indexada) para detección de producto",
    min_value=1,
    max_value=5000,
    step=1,
    key="product_band",
)
st.caption(
    "Valores por defecto: banda 10 para hoja y banda 165 para producto. Los rangos se aplican tras multiplicar la reflectancia por 10000."
)
if not st.session_state.get("product_ranges"):
    st.session_state["product_ranges"] = [
        {"min": 3900.0, "max": 4300.0},
        {"min": 4900.0, "max": 5200.0},
    ]
ranges_editor = st.data_editor(
    st.session_state["product_ranges"],
    num_rows="dynamic",
    hide_index=True,
    column_config={
        "min": st.column_config.NumberColumn("Mínimo", format="%.1f", step=50.0),
        "max": st.column_config.NumberColumn("Máximo", format="%.1f", step=50.0),
    },
    key="product_ranges_editor",
)
clean_ranges: list[dict[str, float]] = []
if isinstance(ranges_editor, list):
    iterable = ranges_editor
elif hasattr(ranges_editor, "to_dict"):
    iterable = ranges_editor.to_dict("records")
else:
    iterable = []
for row in iterable:
    if isinstance(row, dict):
        min_val = row.get("min")
        max_val = row.get("max")
    else:
        try:
            min_val, max_val = row
        except (TypeError, ValueError):
            continue
    if min_val is None or max_val is None:
        continue
    clean_ranges.append({"min": float(min_val), "max": float(max_val)})
st.session_state["product_ranges"] = clean_ranges
if not clean_ranges:
    st.warning("Añade al menos un rango para la detección de producto.")


cols_actions = st.columns(2)
with cols_actions[0]:
    if st.button("Guardar perfil actual"):
        st.session_state["_config_saved"] = {
            "orb_nfeatures": st.session_state["orb_nfeatures"],
            "detection_scale_factor": st.session_state["detection_scale_factor"],
            "ransac_reproj_thresh": st.session_state["ransac_reproj_thresh"],
            "ransac_max_iters": st.session_state["ransac_max_iters"],
            "ransac_confidence": st.session_state["ransac_confidence"],
            "leaf_band": st.session_state["leaf_band"],
            "leaf_threshold": st.session_state["leaf_threshold"],
            "product_band": st.session_state["product_band"],
            "product_ranges": st.session_state["product_ranges"],
        }
        st.success("Perfil guardado en la sesión.")
with cols_actions[1]:
    if st.button("Restaurar valores por defecto"):
        st.session_state.update(
            {
                "orb_nfeatures": 4000,
                "detection_scale_factor": 0.75,
                "ransac_reproj_thresh": 3.0,
                "ransac_max_iters": 5000,
                "ransac_confidence": 0.995,
                "leaf_band": 10,
                "leaf_threshold": 2000.0,
                "product_band": 165,
                "product_ranges": [
                    {"min": 3900.0, "max": 4300.0},
                    {"min": 4900.0, "max": 5200.0},
                ],
            }
        )
        st.info("Se restauraron los valores por defecto.")
