from __future__ import annotations

from pathlib import Path
import typer

from .pipeline import process_pair, export_outputs


app = typer.Typer(help="CLI del pipeline EcoVid")


@app.command("run")
def run(
    sin_hdr: Path = typer.Option(..., exists=True, readable=True, help="Ruta al .hdr de la imagen SIN"),
    sin_bil: Path = typer.Option(..., exists=True, readable=True, help="Ruta al .bil de la imagen SIN"),
    con_hdr: Path = typer.Option(..., exists=True, readable=True, help="Ruta al .hdr de la imagen CON"),
    con_bil: Path = typer.Option(..., exists=True, readable=True, help="Ruta al .bil de la imagen CON"),
    outdir: Path = typer.Option("salida", help="Carpeta de salida"),
    stem: str = typer.Option("resultado", help="Prefijo base de los archivos de salida"),
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


