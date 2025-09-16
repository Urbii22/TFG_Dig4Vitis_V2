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


cols_actions = st.columns(2)
with cols_actions[0]:
    if st.button("Guardar perfil actual"):
        st.session_state["_config_saved"] = {
            "orb_nfeatures": st.session_state["orb_nfeatures"],
            "detection_scale_factor": st.session_state["detection_scale_factor"],
            "ransac_reproj_thresh": st.session_state["ransac_reproj_thresh"],
            "ransac_max_iters": st.session_state["ransac_max_iters"],
            "ransac_confidence": st.session_state["ransac_confidence"],
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
            }
        )
        st.info("Se restauraron los valores por defecto.")
