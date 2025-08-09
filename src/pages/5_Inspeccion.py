import io

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from spectral.io import envi

st.set_page_config(page_title="EcoVid – Inspección", layout="wide")
st.title("Inspección y Curvas Espectrales")

if not st.session_state.get("processed"):
    st.info("Procesa primero un par en la página Procesar.")
    st.stop()

hdr_sin = st.session_state.get("hdr_sin_path")
bil_sin = st.session_state.get("bil_sin_path")
hdr_con = st.session_state.get("hdr_con_path")
bil_con = st.session_state.get("bil_con_path")

if not (hdr_sin and bil_sin and hdr_con and bil_con):
    st.warning("No hay rutas de los cubos disponibles.")
    st.stop()

ds_sin = envi.open(hdr_sin, bil_sin)
ds_con = envi.open(hdr_con, bil_con)

st.markdown("Selecciona un píxel o un ROI pequeño para ver la curva espectral (SIN/CON).")
col1, col2 = st.columns(2)

with col1:
    st.image(st.session_state["rgb_sin"], caption="SIN (RGB)")
with col2:
    st.image(st.session_state["rgb_con"], caption="CON (RGB)")

row = st.number_input("Fila (y)", min_value=0, max_value=int(ds_sin.shape[0]) - 1, value=0)
col = st.number_input("Columna (x)", min_value=0, max_value=int(ds_sin.shape[1]) - 1, value=0)
roi = st.slider("Tamaño ROI (lado)", 1, 15, 1, 2)


def spectra_at(ds, r, c, s):
    r0 = max(0, int(r) - s // 2)
    c0 = max(0, int(c) - s // 2)
    r1 = min(ds.shape[0], r0 + s)
    c1 = min(ds.shape[1], c0 + s)
    cube = ds[r0:r1, c0:c1, :]
    # media sobre ROI
    return cube.mean(axis=(0, 1))


spec_sin = spectra_at(ds_sin, row, col, roi)
spec_con = spectra_at(ds_con, row, col, roi)

wl = np.array([float(x) for x in ds_sin.bands.centers])

fig = go.Figure()
fig.add_trace(go.Scatter(x=wl, y=spec_sin, mode="lines", name="SIN"))
fig.add_trace(go.Scatter(x=wl, y=spec_con, mode="lines", name="CON"))
fig.update_layout(
    height=400,
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis_title="Longitud de onda (nm)",
    yaxis_title="Intensidad",
)
st.plotly_chart(fig, use_container_width=True)

csv_bytes = io.BytesIO()
csv_bytes.write(b"wavelength,sin,con\n")
for x, a, b in zip(wl, spec_sin, spec_con, strict=False):
    csv_bytes.write(f"{x},{a},{b}\n".encode())

st.download_button(
    "Exportar CSV curva espectral",
    csv_bytes.getvalue(),
    file_name="curva_espectral.csv",
    mime="text/csv",
)
