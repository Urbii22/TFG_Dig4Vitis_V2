import streamlit as st
import os
import atexit
import base64
from funciones.interfaz import cargar_video

# ¡Coloca esta llamada inmediatamente después de importar streamlit!
st.set_page_config(
    page_title="Dig4Vitis",
    page_icon="🍇",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    # Aplicar estilos globales desde el archivo CSS
    try:
        with open("estilos.css") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("No se han aplicado estilos globales (no se encontró estilos.css).")

    # Encabezado principal centrado
    st.markdown("<h1 style='text-align: center;'>Evaluación inteligente y en tiempo real de la deposición de pesticidas en viñedo mediante procesamiento de imágenes (DIG4VITIS)</h1>", unsafe_allow_html=True)
    
    # Llamada a la interfaz que muestra el vídeo streaming y la captura de la cámara
    cargar_video()
    
    # Footer con múltiples logos y texto
    logos = [
        ("imagen_logo_UE.png",  "ue-logo"),   # se mostrará a 360px de ancho
        ("escudo_ubu.jpg",      "ubu-logo"),  # 120px de ancho
        ("gicap_logo.jpeg",     "gicap-logo") # 120px de ancho
    ]
    img_tags = []
    for filename, css_class in logos:
        path = os.path.abspath(os.path.join("recursos", filename))
        if os.path.exists(path):
            with open(path, "rb") as img_file:
                img_bytes = img_file.read()
            img_b64 = base64.b64encode(img_bytes).decode()
            mime = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
            width = "360px" if filename == "imagen_logo_UE.png" else "120px"
            img_tags.append(
                f"<img src='data:{mime};base64,{img_b64}' "
                f"class='{css_class}' "
                f"style='width:{width}; height:auto; vertical-align:middle; margin:0 10px;' "
                f"alt='{filename}'/>"
            )
    footer_html = f"""
    <footer style='text-align: center; padding: 10px; margin-top: 20px;'>
        {''.join(img_tags)}
        <span>© 2025 | TFG Universidad de Burgos</span>
    </footer>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
