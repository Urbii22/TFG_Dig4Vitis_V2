import os
import streamlit as st

def limpiar_carpeta():
    """Limpia la carpeta 'archivos_subidos' al cerrar la aplicación."""
    carpeta = 'archivos_subidos'
    if os.path.exists(carpeta):
        for archivo in os.listdir(carpeta):
            ruta_archivo = os.path.join(carpeta, archivo)
            os.unlink(ruta_archivo)

def guardar_archivos_subidos(archivos_subidos):
    """
    Guarda los archivos subidos y retorna las rutas de los archivos .bil y .bil.hdr.
    """
    hdr_file = None
    bil_file = None
    nombre_hyper = ""
    
    with st.spinner("Procesando archivos..."):
        for archivo in archivos_subidos:
            ruta_archivos = os.path.join('archivos_subidos', archivo.name)
            with open(ruta_archivos, 'wb') as f:
                f.write(archivo.read())
            if archivo.name.endswith('.bil.hdr'):
                hdr_file = ruta_archivos
            elif archivo.name.endswith('.bil'):
                bil_file = ruta_archivos
                nombre_hyper = os.path.splitext(archivo.name)[0]
                st.markdown(f"""
                    <div style="background-color: #303030; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <p style="color: #a5d6a7; font-weight: 600; margin: 0;">
                            Archivo cargado: {nombre_hyper}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
    return hdr_file, bil_file, nombre_hyper
