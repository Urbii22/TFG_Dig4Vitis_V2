import datetime
import cv2
import streamlit as st
import spectral
import numpy as np
from streamlit_image_zoom import image_zoom
from funciones.archivos import guardar_archivos_subidos
from funciones.procesamiento import aplicar_procesamiento, realizar_post_procesamiento
from funciones.csv import generar_datos_csv

def cargar_hyper_bin():
    """
    Gestiona la carga de la imagen hiperespectral y el procesamiento asociado.
    Muestra la interfaz para subir archivos, seleccionar el método de umbral,
    procesar la imagen y visualizar los resultados.
    """
    st.markdown("""
        <div style="background-color: #2a2a2a; padding: 15px; border-radius: 10px; border-left: 5px solid #5ab44b; margin-bottom: 20px;">
            <h3 style="color: #a5d6a7; margin-top: 0;">📤 Cargar imagen hiperespectral</h3>
            <p style="color: #e0e0e0; margin-bottom: 5px;">Sube los archivos .bil y .bil.hdr de tu imagen hiperespectral</p>
        </div>
        """, unsafe_allow_html=True)
    
    archivos_subidos = st.file_uploader("Archivos BIL", accept_multiple_files=True, type=["bil", "bil.hdr"], label_visibility="collapsed")
    modo_umbral = st.radio("Selecciona el método de umbral para la detección de cuprocol (Banda 60):",
                           options=["Fijo", "Adaptativo"], index=0)
    
    if len(archivos_subidos) == 2:
        hdr_file, bil_file, nombre_hyper = guardar_archivos_subidos(archivos_subidos)
        if hdr_file and bil_file:
            st.markdown(f"""
                <div style="background-color: #263238; padding: 15px; border-radius: 10px; border-left: 5px solid #81d4fa; margin: 20px 0;">
                    <h4 style="color: #b3e5fc; margin-top: 0;">ℹ️ Información de procesamiento</h4>
                    <ul style="color: #e1f5fe;">
                        <li>Se utilizará la <b>Banda 30</b> para detección de hoja</li>
                        <li>Se utilizará la <b>Banda 60</b> para detección de cuprocol</li>
                        <li>Método de umbral: <b>{modo_umbral}</b></li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("🔍 Procesar imagen", help="Inicia el procesamiento de la imagen hiperespectral"):
                img = spectral.open_image(hdr_file)
                progress_bar = st.progress(0)
                status_text = st.empty()
                status_text.text("Procesando banda 30 para detección de hoja...")
                progress_bar.progress(25)
                status_text.text("Procesando banda 60 para detección de cuprocol...")
                progress_bar.progress(50)
                trinarizada = aplicar_procesamiento(img, modo_umbral)
                status_text.text("Realizando post-procesamiento de la imagen...")
                progress_bar.progress(75)
                trinarizada = realizar_post_procesamiento(trinarizada)
                progress_bar.progress(100)
                status_text.text("¡Procesamiento completado!")
                st.session_state['trinarizada'] = trinarizada
                st.success("La imagen ha sido procesada con éxito!")
                
                # Obtener imagen normal (Banda 30) y crear superposición
                banda_hoja = img.read_band(30)
                banda_hoja_norm = cv2.normalize(banda_hoja, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                imagen_normal = cv2.cvtColor(banda_hoja_norm, cv2.COLOR_GRAY2BGR)
                mask_cupro = (trinarizada[:, :, 0] == 0) & (trinarizada[:, :, 1] == 255) & (trinarizada[:, :, 2] == 0)
                imagen_superpuesta = imagen_normal.copy()
                overlay = np.zeros_like(imagen_normal)
                overlay[mask_cupro] = [0, 255, 0]
                imagen_superpuesta = cv2.addWeighted(imagen_normal, 0.7, overlay, 0.3, 0)
                
                st.markdown("### 🖼️ Visualización de resultados")
                tabs = st.tabs(["🎯 Imagen trinarizada", "📊 Imagen normal", "🔍 Superposición"])
                with tabs[0]:
                    st.markdown("**Imagen trinarizada**")
                    st.markdown("*Zonas negras: hojas, zonas verdes: cuprocol, zonas rojas: fondo*")
                    image_zoom(trinarizada)
                with tabs[1]:
                    st.markdown("**Imagen normal (Banda 30)**")
                    image_zoom(imagen_normal)
                with tabs[2]:
                    st.markdown("**Superposición: detección de cuprocol**")
                    image_zoom(imagen_superpuesta)
                
                st.markdown("""
                <div style="background-color: #2a382a; padding: 15px; border-radius: 10px; border-left: 5px solid #5ab44b; margin-top: 20px;">
                    <h3 style="color: #a5d6a7; margin-top: 0;">📊 Resultados y descargas</h3>
                </div>
                """, unsafe_allow_html=True)
                
                ocultar_fs = '''
                <style>
                button[title="View fullscreen"]{
                    visibility: hidden;}
                </style>
                '''
                colA, colB = st.columns([1, 2])
                with colA:
                    st.image(trinarizada, width=333, caption="Resultado final")
                    st.markdown(ocultar_fs, unsafe_allow_html=True)
                with colB:
                    nombre = st.session_state.get('nombre', '')
                    if not nombre:
                        st.warning("⚠️ Ingresa un nombre para identificar este análisis")
                    generar_datos_csv(trinarizada, nombre_hyper, nombre)
                    if st.session_state.get('trinarizada') is not None and st.button("💾 Guardar análisis", help="Guarda este análisis en la sesión"):
                        fecha = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        if 'trinarizadas_cargadas' not in st.session_state:
                            st.session_state['trinarizadas_cargadas'] = {}
                        st.session_state['trinarizadas_cargadas'][(nombre_hyper, fecha)] = trinarizada
                        st.success(f"✅ Análisis '{nombre_hyper}' guardado correctamente")
                        st.experimental_rerun()
    elif len(archivos_subidos) > 2:
        st.error("❌ Sólo debes subir dos archivos, el .bil y .bil.hdr de la misma imagen.")
    else:
        st.markdown("""
        <div style="background-color: #263238; padding: 15px; border-radius: 10px; border-left: 5px solid #81d4fa; margin-bottom: 15px;">
            <h4 style="color: #b3e5fc; margin: 0;">ℹ️ Instrucciones</h4>
            <p style="color: #e1f5fe; font-weight: 500; margin-top: 8px;">
                Debes subir dos archivos, el .bil y .bil.hdr de la misma imagen.
            </p>
        </div>
        """, unsafe_allow_html=True)

def mostrar_imagenes_trinarizadas():
    """Muestra las imágenes trinarizadas guardadas en la sesión."""
    imagenes = st.session_state.get('trinarizadas_cargadas', {})
    if imagenes:
        st.markdown("""
        <div style="background-color: #e8f5e9; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
            <h4 style="color: #2e7d32; margin: 0;">📂 Análisis guardados</h4>
        </div>
        """, unsafe_allow_html=True)
        for (nombre_hyper, fecha), imagen in imagenes.items():
            with st.expander(f"<span style='color: #0d47a1; font-weight: 600;'>📊 {nombre_hyper} - {fecha}</span>"):
                st.image(imagen, width=200)
                if st.button(f"🔄 Cargar '{nombre_hyper}'", key=f"cargar_{nombre_hyper}_{fecha}"):
                    st.session_state['trinarizada'] = imagen
                    st.info(f"Imagen '{nombre_hyper}' cargada para análisis")
    else:
        st.markdown("""
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px;">
            <h4 style="color: #757575; margin: 0;">📂 No hay análisis guardados</h4>
            <p style="color: #9e9e9e; margin: 5px 0 0 0; font-size: 0.9em;">
                Procesa una imagen y usa "Guardar análisis" para almacenarla aquí.
            </p>
        </div>
        """, unsafe_allow_html=True)
