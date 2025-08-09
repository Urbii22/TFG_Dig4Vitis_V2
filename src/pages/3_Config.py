import os
import sys

import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

st.set_page_config(page_title="EcoVid – Configuración", layout="wide")
st.title("Configuración")

st.write("Parámetros de alineación (aplicados en próximas ejecuciones):")

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

st.info(
    "La app actual aún no aplica estos parámetros; se conectarán al pipeline en el siguiente sprint."
)
