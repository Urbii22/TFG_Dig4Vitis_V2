import os
from pathlib import Path

import streamlit as st

from ecovid.pipeline import export_outputs, process_pair  # type: ignore
from funciones.interfaz import aplicar_tema, render_footer, render_header, render_top_nav

st.set_page_config(page_title="EcoVid – Lotes", layout="wide")

aplicar_tema()
render_header(title="EcoVid", subtitle="Procesamiento por Lotes (beta)")
render_top_nav()

st.markdown(
    "Sube un CSV con columnas: sin_hdr,sin_bil,con_hdr,con_bil; o bien procesa por carpetas."
)
st.caption("Tip: También puedes usar la CLI: `ecovid batch lote.csv --outdir salida_lotes`")

tab_csv, tab_dirs = st.tabs(["Desde CSV", "Desde Carpetas"])
outdir = st.text_input("Carpeta de salida", value="salida_lotes")

with tab_csv:
    csv_file = st.file_uploader("CSV de lotes", type=["csv"])
    if csv_file and st.button("Procesar CSV"):
        import csv
        import io

        reader = csv.DictReader(io.StringIO(csv_file.getvalue().decode("utf-8")))
        out_base = Path(outdir)
        out_base.mkdir(parents=True, exist_ok=True)

        resumen_rows = []
        rows = list(reader)
        total = max(1, len(rows))
        prog = st.progress(0.0)
        for idx, row in enumerate(rows, start=1):
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
            prog.progress(min(1.0, idx / total))

        # Guardar resumen
        import pandas as pd

        df = pd.DataFrame(resumen_rows)
        df.to_csv(out_base / "resumen.csv", index=False)
        st.success(f"Lote completado. Resumen en {out_base / 'resumen.csv'}")

with tab_dirs:
    st.write(
        "Procesa por carpetas seleccionando pares SIN/CON (cada carpeta contiene sus .hdr/.bil)"
    )
    sin_dir = st.text_input("Carpeta de SIN", value="")
    con_dir = st.text_input("Carpeta de CON", value="")
    if st.button("Procesar Carpetas"):
        from glob import glob

        out_base = Path(outdir)
        out_base.mkdir(parents=True, exist_ok=True)

        # Emparejar por nombre base (sin extensión); asumimos nombres similares
        def find_pairs(base_dir: str):
            hdrs = sorted(glob(os.path.join(base_dir, "*.hdr")))
            pairs = {}
            for h in hdrs:
                b = os.path.splitext(os.path.basename(h))[0]
                pairs[b] = {"hdr": h, "bil": os.path.join(base_dir, b + ".bil")}
            return pairs

        sin_pairs = find_pairs(sin_dir)
        con_pairs = find_pairs(con_dir)

        keys = sorted(set(sin_pairs.keys()) & set(con_pairs.keys()))
        resumen_rows = []
        prog = st.progress(0.0)
        for idx, k in enumerate(keys, start=1):
            stem = k
            try:
                sp = sin_pairs[k]
                cp = con_pairs[k]
                res = process_pair(sp["hdr"], sp["bil"], cp["hdr"], cp["bil"])
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
            prog.progress(idx / max(1, len(keys)))

        import pandas as pd

        df = pd.DataFrame(resumen_rows)
        df.to_csv(out_base / "resumen.csv", index=False)
        st.success(f"Lote completado. Resumen en {out_base / 'resumen.csv'}")

render_footer()
