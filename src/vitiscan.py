import os
import datetime
import zipfile
import atexit
import streamlit as st
import cv2
import numpy as np
import spectral
import pandas as pd
from skimage import measure
from streamlit_image_zoom import image_zoom

# Configuración de la página y tema de Streamlit
st.set_page_config(
    page_title="VitiScan - Análisis de Viticultura",
    page_icon="🍇",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Crear carpeta para guardar archivos subidos
os.makedirs('archivos_subidos', exist_ok=True)

# Función para limpiar la carpeta de archivos subidos al cerrar la aplicación
def limpiar_carpeta():
    carpeta = 'archivos_subidos'
    for archivo in os.listdir(carpeta):
        ruta_archivo = os.path.join(carpeta, archivo)
        os.unlink(ruta_archivo)

atexit.register(limpiar_carpeta)

# Función principal de la aplicación
def main():
    procesado = False
    ocultar_fs = '''
    <style>
    button[title="View fullscreen"]{
        visibility: hidden;}
    </style>
    '''

    # Aplicar estilos globales desde CSS
    with open("estilos.css") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    
    # Encabezado bonito adaptado a modo oscuro
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

    def guardar_archivos_subidos(archivos_subidos):
        """Guarda los archivos subidos y retorna las rutas de los archivos .bil y .hdr."""
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

    def aplicar_procesamiento(imagen, modo_umbral="Fijo"):
        """
        Aplica el procesamiento de trinarización utilizando:
        - Banda 30 para detección de hoja (binarizada automáticamente con Otsu)
        - Banda 60 para detección de cuprocol, usando:
              * Umbral fijo: se usan los valores 50 y 800 (convertidos a escala 0-255)
              * Umbral adaptativo: recorre la banda para elegir el umbral que maximiza la detección
        """
        # Procesar banda para detección de hoja (Banda 30)
        banda_hoja = imagen.read_band(30)
        banda_hoja = cv2.normalize(banda_hoja, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        _, hoja_bin = cv2.threshold(banda_hoja, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Procesar banda para detección de cuprocol (Banda 60)
        banda_cuprocol = imagen.read_band(60)
        banda_cuprocol = cv2.normalize(banda_cuprocol, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        
        if modo_umbral == "Fijo":
            # Convertir umbrales fijos de 50 y 800 (escala 0-1000) a escala 0-255
            cupro_min = int(50 * 255 / 1000)   # Aproximadamente 12
            cupro_max = int(800 * 255 / 1000)  # Aproximadamente 204
        else:  # Adaptativo: iteramos para encontrar el mejor umbral
            tolerancia = 0.10  # ±10%
            mejor_T = 0
            max_detectados = -1
            
            # Recorrer posibles umbrales de 0 a 255
            for T_candidate in range(0, 256):
                cupro_min_candidate = int(max(0, T_candidate * (1 - tolerancia)))
                cupro_max_candidate = int(min(255, T_candidate * (1 + tolerancia)))
                mask_candidate = cv2.inRange(banda_cuprocol, cupro_min_candidate, cupro_max_candidate)
                num_detectados = np.count_nonzero(mask_candidate)
                if num_detectados > max_detectados:
                    max_detectados = num_detectados
                    mejor_T = T_candidate
                    
            cupro_min = int(max(0, mejor_T * (1 - tolerancia)))
            cupro_max = int(min(255, mejor_T * (1 + tolerancia)))
        
        # Crear la máscara para detectar cuprocol en la banda 60
        gotas_bin = cv2.inRange(banda_cuprocol, cupro_min, cupro_max)
        
        # Crear imagen trinarizada:
        # Rojo: píxeles sin hoja y sin cuprocol
        # Verde: píxeles sin hoja y con cuprocol detectado
        # Negro: zonas de hoja
        trinarizada = np.zeros((banda_hoja.shape[0], banda_hoja.shape[1], 3), dtype=np.uint8)
        trinarizada[(hoja_bin == 0) & (gotas_bin == 0)] = [255, 0, 0]
        trinarizada[(hoja_bin == 0) & (gotas_bin == 255)] = [0, 255, 0]
        trinarizada[hoja_bin == 255] = [0, 0, 0]
        
        return trinarizada

    def realizar_post_procesamiento(trinarizada):
        """Realiza el post-procesamiento de la imagen trinarizada."""
        mascara_cobre = (trinarizada[:, :, 0] == 255) & (trinarizada[:, :, 1] == 0) & (trinarizada[:, :, 2] == 0)
        mascara_dilatada = cv2.dilate(mascara_cobre.astype(np.uint8), np.ones((5, 5), np.uint8), iterations=1)
        mascara_rellenada = cv2.morphologyEx(mascara_dilatada, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        mascara_final = cv2.erode(mascara_rellenada, np.ones((3, 3), np.uint8), iterations=1)
        
        etiquetas = measure.label(mascara_final, connectivity=2)
        propiedades = measure.regionprops(etiquetas)
        
        area_min_umbral = 100
        area_max_umbral = 500
        
        trinarizada[(mascara_final == 1) & ~mascara_cobre] = [255, 0, 0]
        for prop in propiedades:
            if prop.area > area_max_umbral or prop.area < area_min_umbral:
                for coord in prop.coords:
                    trinarizada[coord[0], coord[1]] = [0, 255, 0]
        return trinarizada

    def generar_datos_csv(trinarizada, nombre_hyper, nombre):
        """Genera y descarga los archivos CSV de la imagen trinarizada."""
        total_pixeles = trinarizada.shape[0] * trinarizada.shape[1]
        num_pixeles_hoja = np.count_nonzero(np.all(trinarizada == [0, 255, 0], axis=-1))
        num_pixeles_cobre = np.count_nonzero(np.all(trinarizada == [255, 0, 0], axis=-1))
        
        df = pd.DataFrame({
            'Métrica': ['Pixeles Hoja', 'Pixeles Cuprocol'],
            'Cantidad': [num_pixeles_hoja, num_pixeles_cobre],
            'Porcentaje': [
                f"{round(num_pixeles_hoja / total_pixeles * 100, 2)}%",
                f"{round(num_pixeles_cobre / num_pixeles_hoja * 100, 2)}%" if num_pixeles_hoja != 0 else "0%"
            ],
        })
        st.markdown("<h3 style='color: #1e3a8a;'>📊 Resultados del análisis</h3>", unsafe_allow_html=True)
        st.dataframe(df)
        
        _, buffer_imagen = cv2.imencode('.png', cv2.cvtColor(trinarizada, cv2.COLOR_RGB2BGR))
        imagen_bytes = buffer_imagen.tobytes()
        csv_porc_str = df.to_csv(index=False)
        
        st.download_button(
            label="📊 Descargar CSV de porcentajes",
            data=csv_porc_str,
            file_name=f"PORCSV_{nombre}_{nombre_hyper}.csv",
            mime="text/csv",
            help="Descarga un archivo CSV con los porcentajes de la imagen trinarizada"
        )
        st.download_button(
            label="🖼️ Descargar imagen trinarizada",
            data=imagen_bytes,
            file_name=f"TRINA_{nombre}_{nombre_hyper}.png",
            mime="image/png",
            help="Descarga la imagen trinarizada en formato PNG"
        )
        if st.button("📋 Crear CSV trinarizado", help="Genera un CSV detallado pixel por pixel"):
            alto, ancho, _ = trinarizada.shape
            output_csv = []
            with st.spinner("Generando CSV detallado..."):
                for x in range(alto):
                    fila = []
                    for y in range(ancho):
                        color_pixel = trinarizada[x, y]
                        if np.array_equal(color_pixel, [0, 0, 0]):
                            valor = '00'
                        elif np.array_equal(color_pixel, [0, 255, 0]):
                            valor = '01'
                        elif np.array_equal(color_pixel, [255, 0, 0]):
                            valor = '10'
                        fila.append(valor)
                    output_csv.append(fila)
                output_csv_str = '\n'.join([','.join(row) for row in output_csv])
                st.download_button(
                    label="📥 Descargar CSV trinarizado",
                    data=output_csv_str,
                    file_name=f"TRINACSV_{nombre}_{nombre_hyper}.csv",
                    mime="text/csv"
                )

    def cargar_hyper_bin():
        """Carga una imagen hiperespectral y realiza la trinarización utilizando el método de umbral seleccionado."""
        st.markdown("""
        <div style="background-color: #2a2a2a; padding: 15px; border-radius: 10px; border-left: 5px solid #5ab44b; margin-bottom: 20px;">
            <h3 style="color: #a5d6a7; margin-top: 0;">📤 Cargar imagen hiperespectral</h3>
            <p style="color: #e0e0e0; margin-bottom: 5px;">Sube los archivos .bil y .bil.hdr de tu imagen hiperespectral</p>
        </div>
        """, unsafe_allow_html=True)
        
        archivos_subidos = st.file_uploader("Archivos BIL", accept_multiple_files=True, type=["bil", "bil.hdr"], label_visibility="collapsed")
        
        # Seleccionar el método de umbral
        modo_umbral = st.radio("Selecciona el método de umbral para la detección de cuprocol (Banda 60):",
                               options=["Fijo", "Adaptativo"], index=0)
        
        if len(archivos_subidos) == 2:
            hdr_file, bil_file, nombre_hyper = guardar_archivos_subidos(archivos_subidos)
            if hdr_file and bil_file:
                st.markdown("""
                <div style="background-color: #263238; padding: 15px; border-radius: 10px; border-left: 5px solid #81d4fa; margin: 20px 0;">
                    <h4 style="color: #b3e5fc; margin-top: 0;">ℹ️ Información de procesamiento</h4>
                    <ul style="color: #e1f5fe;">
                        <li>Se utilizará la <b>Banda 30</b> para detección de hoja</li>
                        <li>Se utilizará la <b>Banda 60</b> para detección de cuprocol</li>
                        <li>Método de umbral: <b>{modo_umbral}</b></li>
                    </ul>
                </div>
                """.format(modo_umbral=modo_umbral), unsafe_allow_html=True)
                
                if st.button("🔍 Procesar imagen", help="Inicia el procesamiento de la imagen hiperespectral"):
                    img = spectral.open_image(hdr_file)
                    
                    # Actualizar estados de progreso
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("Procesando banda 30 para detección de hoja...")
                    progress_bar.progress(25)
                    
                    status_text.text("Procesando banda 60 para detección de cuprocol...")
                    progress_bar.progress(50)
                    
                    # Aplicar procesamiento principal con el método seleccionado
                    trinarizada = aplicar_procesamiento(img, modo_umbral)
                    
                    status_text.text("Realizando post-procesamiento de la imagen...")
                    progress_bar.progress(75)
                    
                    trinarizada = realizar_post_procesamiento(trinarizada)
                    
                    progress_bar.progress(100)
                    status_text.text("¡Procesamiento completado!")
                    st.session_state['trinarizada'] = trinarizada
                    
                    st.success("La imagen ha sido procesada con éxito!")
                    
                    # Obtener la imagen normal a partir de la banda 30
                    banda_hoja = img.read_band(30)
                    banda_hoja_norm = cv2.normalize(banda_hoja, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                    imagen_normal = cv2.cvtColor(banda_hoja_norm, cv2.COLOR_GRAY2BGR)
                    
                    # Crear imagen superpuesta resaltando la detección de cuprocol (en verde)
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
                    
                    colA, colB = st.columns([1, 2])
                    with colA:
                        st.image(trinarizada, width=333, caption="Resultado final")
                        st.markdown(ocultar_fs, unsafe_allow_html=True)
                    with colB:
                        nombre = st.session_state.get('nombre', '')
                        if not nombre:
                            st.warning("⚠️ Ingresa un nombre para identificar este análisis")
                        generar_datos_csv(trinarizada, nombre_hyper, nombre)
                        if st.session_state.get('trinarizada') is not None and st.button("💾 Guardar análisis", 
                                                                                         help="Guarda este análisis en la sesión"):
                            fecha = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            if 'trinarizadas_cargadas' not in st.session_state:
                                st.session_state['trinarizadas_cargadas'] = {}
                            st.session_state['trinarizadas_cargadas'][(nombre_hyper, fecha)] = trinarizada
                            st.success(f"✅ Análisis '{nombre_hyper}' guardado correctamente")
                            st.experimental_rerun()
        elif len(archivos_subidos) > 2:
            st.error("❌ Sólo debes subir dos archivos, el .bil y el .bil.hdr de la misma imagen.")
        else:
            st.markdown("""
            <div style="background-color: #263238; padding: 15px; border-radius: 10px; border-left: 5px solid #81d4fa; margin-bottom: 15px;">
                <h4 style="color: #b3e5fc; margin: 0;">ℹ️ Instrucciones</h4>
                <p style="color: #e1f5fe; font-weight: 500; margin-top: 8px;">
                    Debes subir dos archivos, el .bil y el .bil.hdr de la misma imagen.
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

    # Interfaz principal: dos columnas, una para cargar la imagen y otra para ver los análisis guardados
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
        
        st.markdown("""
        <div style="background-color: #f0f4fa; padding: 15px; border-radius: 10px; margin-top: 20px;">
            <h4 style="color: #1e3a8a; margin-top: 0;">ℹ️ Ayuda</h4>
            <p style="font-size: 0.9em; color: #4a5568;">
                VitiScan te permite analizar imágenes hiperespectrales para detectar cuprocol en hojas de vid.
                <ul style="font-size: 0.85em; color: #4a5568;">
                    <li>Sube los archivos .bil y .bil.hdr</li>
                    <li>Elige el método de umbral para la detección de cuprocol (Banda 60): Fijo o Adaptativo</li>
                    <li>Ingresa un nombre identificativo</li>
                    <li>Procesa la imagen y descarga los resultados en CSV o PNG</li>
                </ul>
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 10px; font-size: 0.8em;'>
        <p>VitiScan - Análisis de viticultura de precisión mediante imágenes hiperespectrales</p>
        <p>© 2025 | Desarrollado para TFG Universidad de Burgos</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
