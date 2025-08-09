import os
import sys
from pathlib import Path

import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ecovid.pipeline import export_outputs, process_pair  # type: ignore  # noqa: E402

st.set_page_config(page_title="EcoVid – Lotes", layout="wide")
st.title("Procesamiento por Lotes (beta)")

st.markdown(
    "Sube un CSV con columnas: sin_hdr,sin_bil,con_hdr,con_bil; se generarán salidas en una carpeta."
)
st.caption("Tip: También puedes usar la CLI: `ecovid batch lote.csv --outdir salida_lotes`")

csv_file = st.file_uploader("CSV de lotes", type=["csv"])  # futuro: permitir carpeta
outdir = st.text_input("Carpeta de salida", value="salida_lotes")

if csv_file and st.button("Procesar Lote"):
    import csv
    import io

    reader = csv.DictReader(io.StringIO(csv_file.getvalue().decode("utf-8")))
    out_base = Path(outdir)
    out_base.mkdir(parents=True, exist_ok=True)

    resumen_rows = []
    for idx, row in enumerate(reader, start=1):
        stem = f"item_{idx:03d}"
        try:
            res = process_pair(row["sin_hdr"], row["sin_bil"], row["con_hdr"], row["con_bil"])
            png, mask, csvp = export_outputs(res, out_base / stem, stem)
            resumen_rows.append(
                {
                    "stem": stem,
                    "png": str(png),
                    "mask": str(mask),
                    "csv": str(csvp),
                    "coverage": f"{res.coverage_percent:.2f}",
                }
            )
        except Exception as e:
            resumen_rows.append({"stem": stem, "error": str(e)})

    # Guardar resumen
    import pandas as pd

    df = pd.DataFrame(resumen_rows)
    df.to_csv(out_base / "resumen.csv", index=False)
    st.success(f"Lote completado. Resumen en {out_base / 'resumen.csv'}")
