import os
import atexit
import streamlit as st
from funciones.archivos import limpiar_carpeta
from funciones.interfaz import cargar_hyper_bin

# Configuración de la página
st.set_page_config(
    page_title="VitiScan - Análisis de Viticultura",
    page_icon="🍇",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Crear carpeta para archivos subidos
os.makedirs('archivos_subidos', exist_ok=True)
atexit.register(limpiar_carpeta)

def main():
    # Aplicar estilos globales desde el archivo CSS
    with open("estilos.css") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    
    # Encabezado simplificado
    st.markdown("<h1 style='text-align: center;'>🍇 VitiScan: Análisis de Viticultura</h1>", unsafe_allow_html=True)
    
    # Interfaz simplificada con solo dos botones e imágenes dispuestas en dos columnas
    cargar_hyper_bin()
    
    # Footer simple
    st.markdown(
        "<footer style='text-align: center; padding: 10px; margin-top: 20px;'>© 2025 | TFG Universidad de Burgos</footer>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
