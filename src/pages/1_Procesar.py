import streamlit as st

from ecovid.report import build_pdf_report, build_zip_report
from funciones.interfaz import (
    mostrar_previsualizacion_y_resultados,
    mostrar_subida_archivos,
)

st.set_page_config(page_title="EcoVid – Procesar", layout="wide")
st.title("Procesamiento de Imágenes")

mostrar_subida_archivos()
if st.session_state.get("processed", False):
    mostrar_previsualizacion_y_resultados()
    # Botones de exportación
    colz1, colz2 = st.columns(2)
    with colz1:
        if st.button("📦 Exportar reporte ZIP", use_container_width=True):
            res = st.session_state["resultado_final"]
            hoja = st.session_state["hoja_comun"]
            gotas = st.session_state["gotas_final"]
            pct = float((gotas.sum() / hoja.sum()) * 100.0) if hoja.sum() else 0.0
            zpath = build_zip_report(
                result_image_rgb=res,
                final_drops_mask=gotas,
                coverage_percent=pct,
                metrics=st.session_state.get("align_metrics", {}),
                output_zip="reporte.zip",
            )
            with open(zpath, "rb") as f:
                st.download_button(
                    "Descargar ZIP", f, file_name="reporte.zip", mime="application/zip"
                )
    with colz2:
        pdf_bytes = build_pdf_report(
            result_image_rgb=st.session_state["resultado_final"],
            final_drops_mask=st.session_state["gotas_final"],
            coverage_percent=(
                float(
                    (st.session_state["gotas_final"].sum() / st.session_state["hoja_comun"].sum())
                    * 100.0
                )
                if st.session_state["hoja_comun"].sum()
                else 0.0
            ),
            metrics=st.session_state.get("align_metrics", {}),
        )
        st.download_button(
            "🖨️ Exportar PDF",
            data=pdf_bytes,
            file_name="reporte.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
