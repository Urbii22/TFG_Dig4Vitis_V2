import streamlit as st

st.set_page_config(page_title="EcoVid – Ayuda", layout="wide")
st.title("Ayuda")

st.markdown(
    """
    - Carga pares ENVI correctos: cada imagen requiere `.bil` y `.hdr`.
    - Tras procesar se muestran métricas: porcentaje de recubrimiento, inliers, ratio y error.
    - Usa la página de Lotes para procesar múltiples pares mediante CSV.
    - La CLI `ecovid run` permite ejecutar el pipeline sin UI.
    """
)
