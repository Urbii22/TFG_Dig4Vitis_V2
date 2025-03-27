import cv2
import pandas as pd
import numpy as np
import streamlit as st

def generar_datos_csv(trinarizada, nombre_hyper, nombre):
    """Genera y ofrece la descarga de los CSV e imágenes resultantes del análisis."""
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
                    if (color_pixel == [0, 0, 0]).all():
                        valor = '00'
                    elif (color_pixel == [0, 255, 0]).all():
                        valor = '01'
                    elif (color_pixel == [255, 0, 0]).all():
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
