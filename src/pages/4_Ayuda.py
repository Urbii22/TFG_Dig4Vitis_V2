import streamlit as st

from funciones.interfaz import aplicar_tema, render_footer, render_header, render_top_nav

st.set_page_config(page_title="EcoVid – Ayuda", layout="wide")

aplicar_tema()
render_header(title="EcoVid", subtitle="Ayuda")
render_top_nav()

st.markdown("---")
st.markdown(
    """
    - Carga pares ENVI correctos: cada imagen requiere `.bil` y `.hdr`.
    - Tras procesar se muestran métricas: porcentaje de recubrimiento, inliers, ratio y error.
    - Usa la página de Lotes para procesar múltiples pares mediante CSV.
    - La CLI `ecovid run` permite ejecutar el pipeline sin UI.
    """
)

render_footer()
