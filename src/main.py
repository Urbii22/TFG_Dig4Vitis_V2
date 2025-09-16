import atexit
import os

import streamlit as st

from funciones.archivos import get_temp_dir, limpiar_carpeta
from funciones.interfaz import aplicar_tema, render_footer, render_header, render_top_nav

# Se define la ruta al logo como una constante
LOGO_PATH = os.path.join(os.path.dirname(__file__), "recursos", "EcoVid_logo.png")


# --- Configuración de la Página ---
st.set_page_config(
    page_title="EcoVid",
    page_icon=LOGO_PATH,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Gestión de Archivos Temporales ---
archivos_subidos_dir = get_temp_dir()
atexit.register(lambda: limpiar_carpeta(archivos_subidos_dir))


def main():
    # Tema y cabecera unificados
    aplicar_tema()
    render_header(
        title="EcoVid",
        subtitle="Herramienta para segmentar imágenes hiperespectrales y cuantificar recubrimiento de cobre",
    )
    render_top_nav()

    # Sección principal (Acerca y llamada a la acción)
    st.markdown("---")
    col_a, col_b = st.columns([1.2, 1])
    with col_a:
        st.subheader("¿Qué es EcoVid?")
        st.markdown(
            """
            EcoVid permite analizar pares de imágenes hiperespectrales (SIN/CON tratamiento) para estimar
            el porcentaje de recubrimiento de cobre sobre la superficie foliar. El flujo integra alineación ORB+RANSAC,
            reducción de falsos positivos y exportación de resultados.
            """
        )
        st.page_link("pages/1_Procesar.py", label="Comenzar a procesar", icon="🚀")
    with col_b:
        st.subheader("Funciones destacadas")
        st.markdown(
            "- Procesamiento guiado y por lotes\n- Métricas de alineación\n- Exportación a ZIP y PDF"
        )

    render_footer()


if __name__ == "__main__":
    main()
