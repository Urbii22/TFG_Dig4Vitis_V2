from __future__ import annotations

from pathlib import Path

import typer

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


if __name__ == "__main__":
    app()
