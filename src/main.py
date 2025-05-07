import os
import atexit
import base64
import streamlit as st
from funciones.archivos import limpiar_carpeta
from funciones.interfaz import cargar_hyper_bin

# Configuración de la página
st.set_page_config(
    page_title="Dig4Vitis",
    page_icon="🍇",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Crear carpeta para archivos subidos
os.makedirs('archivos_subidos', exist_ok=True)
atexit.register(limpiar_carpeta)

def main():
    # Aplicar estilos globales desde el archivo CSS
    base_dir = os.path.dirname(__file__)
    css_path = os.path.join(base_dir, "estilos.css")
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"No se encontró el archivo de estilos: {css_path}")
    
    # Encabezado simplificado
    st.markdown("<h1 style='text-align: center;'>Dig4Vitis</h1>", unsafe_allow_html=True)
    
    # Interfaz simplificada con solo dos botones e imágenes dispuestas en dos columnas
    cargar_hyper_bin()
    
    # Footer con múltiples logos y texto
    logos = [
        ("imagen_logo_UE.png", "logo-ue"),
        ("escudo_ubu.jpg", "logo-ubu"),
        ("gicap_logo.jpeg", "logo-gicap")
    ]
    img_tags = []
    for filename, css_class in logos:
        img_path = os.path.abspath(os.path.join("./recursos", filename))
        if os.path.exists(img_path):
            with open(img_path, "rb") as img_file:
                img_bytes = img_file.read()
            img_b64 = base64.b64encode(img_bytes).decode()
            # Determinar tipo MIME según extensión
            mime = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
            # Ajustar ancho según el logo
            width = "360px" if filename == "imagen_logo_UE.png" else "120px"
            img_tag = (
                f"<img src='data:{mime};base64,{img_b64}' "
                f"class='{css_class}' style='width:{width}; height:auto; vertical-align:middle; margin:0 10px;' alt='{filename}'/>"
            )
            img_tags.append(img_tag)
    # Construir footer HTML
    footer_html = f"""
    <footer style='text-align: center; padding: 10px; margin-top: 20px;'>
        {''.join(img_tags)}
        <span>© 2025 | TFG Universidad de Burgos</span>
    </footer>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
