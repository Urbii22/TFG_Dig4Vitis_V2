from __future__ import annotations

from pathlib import Path

import typer

from .demo import write_envi_pair
from .pipeline import export_outputs, process_pair

app = typer.Typer(help="CLI del pipeline EcoVid")


# Opciones definidas a nivel de módulo (cumple B008 de Ruff)
OPT_SIN_HDR = typer.Option(..., exists=True, readable=True, help="Ruta al .hdr de la imagen SIN")
OPT_SIN_BIL = typer.Option(..., exists=True, readable=True, help="Ruta al .bil de la imagen SIN")
OPT_CON_HDR = typer.Option(..., exists=True, readable=True, help="Ruta al .hdr de la imagen CON")
OPT_CON_BIL = typer.Option(..., exists=True, readable=True, help="Ruta al .bil de la imagen CON")
OPT_OUTDIR = typer.Option("salida", help="Carpeta de salida")
OPT_STEM = typer.Option("resultado", help="Prefijo base de los archivos de salida")


@app.command("run")
def run(
    sin_hdr: Path = OPT_SIN_HDR,
    sin_bil: Path = OPT_SIN_BIL,
    con_hdr: Path = OPT_CON_HDR,
    con_bil: Path = OPT_CON_BIL,
    outdir: Path = OPT_OUTDIR,
    stem: str = OPT_STEM,
):
    """Procesa un par de imágenes ENVI y exporta PNG, máscara y CSV."""
    result = process_pair(
        hdr_without=sin_hdr, bil_without=sin_bil, hdr_with=con_hdr, bil_with=con_bil
    )
    png_path, mask_path, csv_path = export_outputs(result, outdir, stem)
    typer.echo(f"✅ PNG anotado: {png_path}")
    typer.echo(f"✅ Máscara:     {mask_path}")
    typer.echo(f"✅ CSV:         {csv_path}")


ARG_CSV = typer.Argument(
    ..., exists=True, readable=True, help="CSV con columnas sin_hdr,sin_bil,con_hdr,con_bil"
)
OPT_OUTDIR_BATCH = typer.Option("salida_lotes", help="Carpeta base de salida")


@app.command("batch")
def batch(
    csv_path: Path = ARG_CSV,
    outdir: Path = OPT_OUTDIR_BATCH,
):
    """Procesa múltiples pares indicados en un CSV y genera un resumen."""
    import csv as _csv

    import pandas as _pd

    rows = list(_csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()))
    outdir.mkdir(parents=True, exist_ok=True)
    resumen = []
    for idx, row in enumerate(rows, start=1):
        stem = f"item_{idx:03d}"
        try:
            res = process_pair(row["sin_hdr"], row["sin_bil"], row["con_hdr"], row["con_bil"])
            png, mask, csvp = export_outputs(res, outdir / stem, stem)
            resumen.append(
                {
                    "stem": stem,
                    "png": str(png),
                    "mask": str(mask),
                    "csv": str(csvp),
                    "coverage": res.coverage_percent,
                }
            )
        except Exception as e:
            resumen.append({"stem": stem, "error": str(e)})
    _pd.DataFrame(resumen).to_csv(outdir / "resumen.csv", index=False)
    typer.echo(f"✅ Lote completado en {outdir}")


if __name__ == "__main__":
    app()
# Registrar un comando extra para generar un dataset demo (opciones a nivel módulo para B008)
OPT_DEMO_OUTDIR = typer.Option("demo_data", help="Carpeta de salida para datos demo")


@app.command("demo")
def demo(outdir: Path = OPT_DEMO_OUTDIR):
    paths = write_envi_pair(outdir)
    typer.echo(f"SIN: {paths.sin_hdr} / {paths.sin_bil}")
    typer.echo(f"CON: {paths.con_hdr} / {paths.con_bil}")
