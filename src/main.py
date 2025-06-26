import os
import base64
import atexit
import streamlit as st
from funciones.archivos import limpiar_carpeta
from funciones.interfaz import (
    mostrar_subida_archivos,
    mostrar_previsualizacion_y_resultados,
)

# Se define la ruta al logo como una constante
LOGO_PATH = os.path.join(os.path.dirname(__file__), 'recursos', 'EcoVid_logo.png')


# --- Configuración de la Página ---
st.set_page_config(
    page_title="EcoVid",
    page_icon=LOGO_PATH, 
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Gestión de Archivos Temporales ---
archivos_subidos_dir = os.path.join(os.path.dirname(__file__), "archivos_subidos")
os.makedirs(archivos_subidos_dir, exist_ok=True)
atexit.register(lambda: limpiar_carpeta(archivos_subidos_dir))

# --- Cargar Estilos CSS ---
def cargar_css():
    base_dir = os.path.dirname(__file__)
    css_path = os.path.join(base_dir, "estilos.css")
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"No se encontró el archivo de estilos en: {css_path}")

# --- Footer ---
def mostrar_footer():
    logos = [
        ("imagen_logo_UE.png", "logo-ue"),
        ("escudo_ubu.jpg", "logo-ubu"),
        ("gicap_logo.jpeg", "logo-gicap"),
    ]
    img_tags = []
    
    for filename, css_class in logos:
        base_dir = os.path.dirname(__file__)
        img_path = os.path.join(base_dir, 'recursos', filename)

        if os.path.exists(img_path):
            try:
                with open(img_path, "rb") as img_file:
                    img_b64 = base64.b64encode(img_file.read()).decode()
                mime = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
                img_tags.append(
                    f"<img src='data:{mime};base64,{img_b64}' class='{css_class}' alt='{filename}'/>"
                )
            except Exception as e:
                st.warning(f"Error al procesar el logo {filename}: {e}")
        else:
            st.warning(f"Advertencia: No se encontró el logo en la ruta esperada: {img_path}")

    footer_html = f"""
    <footer>
        {''.join(img_tags)}
        <p style='margin-top: 15px;'>© 2025 | TFG Universidad de Burgos</p>
    </footer>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

# --- Función Principal ---
def main():
    cargar_css()

    try:
        with open(LOGO_PATH, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()

        header_html = f"""
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 20px;">
            <img src="data:image/png;base64,{logo_b64}" alt="EcoVid Logo" style="width: 75px; height: auto; margin-right: 20px;">
            <h1 style='color: #4CAF50; margin: 0; text-align: left; font-size: 3.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.1);'>EcoVid</h1>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)

    except FileNotFoundError:
        st.warning(f"No se encontró el logo en '{LOGO_PATH}'. Mostrando solo el título.")
        st.markdown("<h1 style='text-align: center; color: #4CAF50; font-size: 3.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.1);'>EcoVid</h1>", unsafe_allow_html=True)
    
    st.markdown("<p style='text-align: center; margin-top: -15px;'>Herramienta para la segmentación de imágenes hiperespectrales y detección de cobre en viñedos.</p>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs([" Cargar y Procesar Imágenes ", " Acerca de "])

    with tab1:
        st.header("Análisis de Imágenes")
        
        with st.container():
            mostrar_subida_archivos()

        if st.session_state.get("processed", False):
            mostrar_previsualizacion_y_resultados()

    with tab2:
        st.header("Sobre el Proyecto EcoVid")
        
        st.subheader("Resumen")
        st.markdown("""
        Este trabajo, enmarcado en el área de la agricultura de precisión, se centra en el desarrollo de una herramienta software para la detección y cuantificación de tratamientos antifúngicos con base de cobre en hojas de viñedo. El objetivo principal es analizar imágenes hiperespectrales para calcular de forma precisa el porcentaje de recubrimiento del producto sobre la superficie foliar.
        
        Para ello, se ha desarrollado esta aplicación web en Python con la biblioteca Streamlit, que permite al usuario procesar dos imágenes hiperespectrales de la misma hoja: una con el tratamiento aplicado y otra sin él. La innovación clave del proyecto reside en la implementación de un algoritmo para la reducción de ruido y falsos positivos. Este sistema utiliza el algoritmo ORB (Oriented FAST and Rotated BRIEF) para alinear automáticamente ambas imágenes, permitiendo sustraer el ruido (variaciones naturales de reflectancia de la propia hoja) de la imagen tratada. Como resultado, la aplicación ofrece una visualización del análisis y el porcentaje de cobertura final, con la opción de descargar los resultados.
        """)

        st.subheader("Objetivos del Proyecto")
        st.markdown("""
        **Objetivos Generales:**
        * Desarrollar una aplicación con una interfaz intuitiva para obtener un resultado visual e inmediato de la eficacia de la aplicación de productos fungicidas con base de cobre.
        * Validar una metodología de análisis de imagen hiperespectral que garantice la obtención de resultados coherentes, fiables y repetibles para su aplicación en entornos de investigación.

        **Objetivos Técnicos:**
        * Construir una aplicación web interactiva en Python utilizando Streamlit que integre todo el flujo de trabajo.
        * Implementar un sistema robusto para la eliminación de falsos positivos basado en la sustracción de ruido, mediante la alineación geométrica precisa con los algoritmos ORB y RANSAC.
        * Habilitar funcionalidades para la exportación de los resultados, tanto las imágenes del análisis como los datos cuantitativos.
        """)

        st.subheader("Metodología")
        st.markdown("""
        1.  **Imágenes Hiperespectrales:** Se utilizan imágenes que, a diferencia de una foto normal (RGB), contienen información de todo el espectro electromagnético para cada píxel, ordenado en 300 bandas. Esto permite identificar la "firma espectral" única del cobre. Los datos se gestionan en formato ENVI, que consta de un fichero `.bil` (datos) y un `.hdr` (metadatos).

        2.  **Trinarización:** Para segmentar la imagen, se realiza un proceso de doble binarización: primero se aísla la hoja del fondo y, sobre el área de la hoja, se detectan los píxeles correspondientes al producto de cobre.

        3.  **Alineamiento y Sustracción de Ruido:** El reto más complejo es diferenciar el producto de las variaciones naturales de la hoja (nervios, brillos) que pueden generar falsos positivos. La solución consiste en alinear la imagen "CON" tratamiento con la imagen "SIN" tratamiento (control) usando el algoritmo ORB, que detecta cientos de puntos característicos en ambas. Luego, RANSAC estima la transformación perfecta entre ellas. Al superponerlas, se puede sustraer el "ruido" natural que aparece en ambas, dejando únicamente el producto real. Se eligió ORB por su alta eficiencia y su licencia de uso libre.
        """)

        st.subheader("Autor y Tutores")
        st.markdown("""
        * **Autor:** Diego Urbaneja Portal
        * **Tutores:** Carlos Cambra Baseca y Ramón Sánchez Alonso
        * **Institución:** Escuela Politécnica Superior, Universidad de Burgos
        """)
    
    mostrar_footer()


if __name__ == "__main__":
    main()