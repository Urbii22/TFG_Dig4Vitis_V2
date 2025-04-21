import streamlit as st


# ¡Coloca esta llamada inmediatamente después de importar streamlit!
st.set_page_config(
    page_title="VitiScan - Análisis de Viticultura",
    page_icon="🍇",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import os
import atexit
from funciones.interfaz import cargar_video


def main():
    # Aplicar estilos globales desde el archivo CSS
    try:
        with open("estilos.css") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning("No se han aplicado estilos globales (no se encontró estilos.css).")

    # Encabezado principal centrado
    st.markdown("<h1 style='text-align: center;'>🍇 VitiScan: Análisis de Viticultura</h1>", unsafe_allow_html=True)
    
    # Llamada a la interfaz que muestra el vídeo  streaming y la captura de la cámara
    cargar_video()
    
    # Footer
    st.markdown(
        "<footer style='text-align: center; padding: 10px; margin-top: 20px;'>© 2025 | TFG Universidad de Burgos</footer>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
