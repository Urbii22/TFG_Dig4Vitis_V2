import streamlit as st

from funciones.interfaz import aplicar_tema, render_footer, render_header, render_top_nav

st.set_page_config(page_title="EcoVid – Inicio", layout="wide")

aplicar_tema()
render_header(
    title="EcoVid",
    subtitle="Inicio",
)
render_top_nav()

st.markdown("---")
st.write(
    "Analiza pares de imágenes hiperespectrales (SIN/CON) para obtener máscara de producto y porcentaje de recubrimiento."
)
st.page_link("pages/1_Procesar.py", label="Ir a Procesar", icon="🚀")

render_footer()
