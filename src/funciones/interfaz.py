import os
import io
from PIL import Image
import streamlit as st


def cargar_imagenes():
    """
    Función para cargar y mostrar imágenes de gotas y su hoja correspondiente con porcentaje de recubrimiento.
    Acepta únicamente archivos JPG (gotas1, gotas2, gotas3) y muestra la imagen relacionada de la carpeta 'hojas'.
    """
    # Directorio del archivo actual (src/funciones)
    base_dir = os.path.dirname(__file__)
    # Directorio raíz del proyecto (src)
    proyecto_dir = os.path.abspath(os.path.join(base_dir, os.pardir))

    # 1. Selector de archivo JPG
    col_selector, col_btn = st.columns([3,1])
    with col_selector:
        archivo_subido = st.file_uploader(
            "Seleccionar imagen de gotas (JPG)",
            type=["jpg", "jpeg"],
            accept_multiple_files=False
        )
    with col_btn:
        procesar = st.button("Procesar")

    if procesar:
        if not archivo_subido:
            st.error("Debes seleccionar una imagen JPG antes de procesar.")
            return

        # Extraer nombre sin extensión
        nombre = os.path.splitext(archivo_subido.name)[0]
        # Mapping de gotas a hoja y porcentaje
        mapping = {
            "gotas1": {"hoja": "hoja1.png", "porcentaje": 8.23},
            "gotas2": {"hoja": "hoja2.png", "porcentaje": 6.85},
            "gotas3": {"hoja": "hoja3.png", "porcentaje": 12.40},
        }

        if nombre not in mapping:
            st.error("El nombre del archivo debe ser 'gotas1', 'gotas2' o 'gotas3'.")
            return

        hoja_info = mapping[nombre]
        hoja_filename = hoja_info["hoja"]
        porcentaje = hoja_info["porcentaje"]

        # Leer bytes de la imagen de gotas
        bytes_gotas = archivo_subido.read()
        imagen_gotas = Image.open(io.BytesIO(bytes_gotas))

        # Ruta de la carpeta 'hojas' en el proyecto
        rutas_hojas = os.path.join(proyecto_dir, "hojas", hoja_filename)
        if not os.path.exists(rutas_hojas):
            st.error(f"No se encontró la imagen de hoja: {hoja_filename}")
            return

        # Leer bytes de la imagen de hoja
        with open(rutas_hojas, "rb") as f:
            bytes_hoja = f.read()
        imagen_hoja = Image.open(io.BytesIO(bytes_hoja))

        # Mostrar resultados
        st.markdown("## Resultados")
        col1, col2 = st.columns(2)
        ancho = 400
        with col1:
            st.image(imagen_gotas, caption=f"Gotas: {archivo_subido.name}", width=ancho)
        with col2:
            st.image(imagen_hoja, caption=f"Hoja: {hoja_filename}", width=ancho)

        # Mostrar porcentaje de recubrimiento
        color = "green" if porcentaje <= 20 else "orange" if porcentaje <= 50 else "red"
        barra_html = f"""
        <div style='margin-top: 20px;'>
            <div style='font-size:18px; font-weight:bold;'>Recubrimiento de cobre: {porcentaje:.2f}%</div>
            <div style='width:100%; background:#e0e0e0; border-radius:5px; overflow:hidden;'>
                <div style='width:{porcentaje}%; height:20px; background:{color};'></div>
            </div>
        </div>
        """
        st.markdown(barra_html, unsafe_allow_html=True)

        # Botones de descarga
        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                "Descargar gotas",
                data=bytes_gotas,
                file_name=archivo_subido.name,
                mime="image/jpeg"
            )
        with dl2:
            mime_tipo = "image/png" if hoja_filename.lower().endswith(".png") else "image/jpeg"
            st.download_button(
                "Descargar hoja",
                data=bytes_hoja,
                file_name=hoja_filename,
                mime=mime_tipo
            )
