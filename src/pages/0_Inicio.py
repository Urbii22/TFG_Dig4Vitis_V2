import base64
import os
import sys

import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

LOGO_PATH = os.path.join(BASE_DIR, "recursos", "EcoVid_logo.png")

st.set_page_config(page_title="EcoVid – Inicio", layout="wide")

try:
    with open(LOGO_PATH, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:16px;">
            <img src="data:image/png;base64,{logo_b64}" width="64"/>
            <h1>EcoVid</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
except FileNotFoundError:
    st.title("EcoVid")

st.write(
    "Analiza pares de imágenes hiperespectrales (SIN/CON tratamiento) para obtener una máscara de producto y el porcentaje de recubrimiento."
)

st.page_link("pages/1_Procesar.py", label="Ir a Procesar", icon="🚀")
