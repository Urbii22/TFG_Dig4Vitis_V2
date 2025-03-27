import os
import atexit
import streamlit as st
from funciones.archivos import limpiar_carpeta
from funciones.interfaz import cargar_hyper_bin, mostrar_imagenes_trinarizadas

# Configuración de la página y tema de Streamlit
st.set_page_config(
    page_title="VitiScan - Análisis de Viticultura",
    page_icon="🍇",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Crear carpeta para guardar archivos subidos
os.makedirs('archivos_subidos', exist_ok=True)

# Registrar la función para limpiar la carpeta al cerrar la aplicación
atexit.register(limpiar_carpeta)

def main():
    # Aplicar estilos globales desde el archivo CSS
    with open("estilos.css") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    
    # Encabezado de la aplicación
    st.markdown("""
    <div style='background: linear-gradient(135deg, #367C2B 0%, #255c1c 100%);
                padding: 1.5rem; 
                border-radius: 15px; 
                margin-bottom: 25px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.3);'>
        <h1 style='color: white; text-align: center; margin-bottom: 5px; font-size: 2.5rem;'>
            🍇 VitiScan: Análisis de Viticultura
        </h1>
        <p style='color: rgba(255,255,255,0.9); text-align: center; font-size: 1.1rem;'>
            Análisis avanzado de imágenes hiperespectrales para viticultura de precisión
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2 = st.columns([7, 2])
    with col1:
        st.markdown("""
        <div style="background-color: #f1f8ff; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
            <h4 style="color: #1e3a8a; margin-top: 0;">👤 Identificación del análisis</h4>
        </div>
        """, unsafe_allow_html=True)
        nombre = st.text_input("Ingresa un nombre para identificar este análisis", 
                             placeholder="Ej: Muestra Viñedo Norte 25/03/2025",
                             help="Este nombre se utilizará para identificar los archivos generados")
        st.session_state['nombre'] = nombre
        cargar_hyper_bin()
    with col2:
        mostrar_imagenes_trinarizadas()
    
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 10px; font-size: 0.8em;'>
        <p>VitiScan - Análisis de viticultura de precisión mediante imágenes hiperespectrales</p>
        <p>© 2025 | Desarrollado para TFG Universidad de Burgos</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
