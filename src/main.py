import os
import atexit
import base64
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
    
    # Footer con logo de la UE y texto
    # Definir ruta absoluta para la imagen
    img_path = os.path.abspath("./recursos/imagen_logo_UE.png")
    if os.path.exists(img_path):
        with open(img_path, "rb") as img_file:
            img_bytes = img_file.read()
        img_b64 = base64.b64encode(img_bytes).decode()
        footer_html = f"""
        <footer style='text-align: center; padding: 10px; margin-top: 20px;'>
            <img src='data:image/png;base64,{img_b64}' style='width:360px; height:auto; vertical-align:middle; margin-right:10px;' alt='Logo UE'/>
            <span>© 2025 | TFG Universidad de Burgos</span>
        </footer>
        """
    else:
        # Si no se encuentra la imagen, mostrar solo el texto
        footer_html = "<footer style='text-align: center; padding: 10px; margin-top: 20px;'>© 2025 | TFG Universidad de Burgos</footer>"
    st.markdown(footer_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
