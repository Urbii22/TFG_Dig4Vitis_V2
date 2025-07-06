import os
import re
import uuid
import streamlit as st


# ------------------------------------------------------------------
# Utilidad interna
# ------------------------------------------------------------------

def _limpiar_base(nombre: str) -> str:
    """
    Extrae el identificador de la muestra desde el inicio del nombre del archivo.
    Ej: "EM 2 (2) cuprantol 133 300823.bil" -> "EM 2 (2)".
    Busca un patrón de letras, espacios y números entre paréntesis.
    """
    # Intenta encontrar el patrón "Letras y números (número)" al inicio.
    # Ej: "EM 2 (2)"
    match = re.match(r'^[A-Za-z\s]+\d+\s\(\d+\)', nombre)
    if match:
        return match.group(0).strip()

    # Si el patrón anterior no funciona, se usa un fallback más simple:
    # Extraer la parte inicial antes del primer número largo (fecha) o palabra clave.
    nombre_sin_ext = os.path.splitext(nombre)[0]
    # Elimina sufijos comunes para no confundirlos con el identificador
    for sufijo in ["_sin", "_con", "-sin", "-con"]:
        if nombre_sin_ext.endswith(sufijo):
            nombre_sin_ext = nombre_sin_ext[:-len(sufijo)]

    # Devuelve la parte inicial como identificador
    return nombre_sin_ext.strip()


# ------------------------------------------------------------------
# API pública
# ------------------------------------------------------------------

def limpiar_carpeta(carpeta: str) -> None:
    """Borra todos los ficheros de la carpeta temporal al cerrar la app."""
    if os.path.exists(carpeta):
        for archivo in os.listdir(carpeta):
            try:
                os.unlink(os.path.join(carpeta, archivo))
            except OSError as e:
                print(f"Error al borrar el archivo {archivo}: {e}")


def guardar_archivos_subidos(archivos_subidos, prefijo: str = ""):
    """
    Guarda los archivos .bil y .bil.hdr seleccionados por el usuario con nombres únicos
    para evitar problemas de caracteres y colisiones.

    Parámetros
    ----------
    archivos_subidos : list[streamlit.UploadedFile]
    prefijo : str
        Texto que se antepone al nombre de cada fichero (p.ej. "sin_" o "con_").

    Devuelve
    -------
    tuple[str | None, str | None, str]
        (ruta_hdr, ruta_bil, nombre_base_muestra)
    """
    hdr_file = bil_file = None
    nombre_base = ""

    os.makedirs("archivos_subidos", exist_ok=True)

    with st.spinner("Procesando archivos..."):
        for archivo in archivos_subidos:
            # Extraer base original (sin extensión)
            base = _limpiar_base(archivo.name)
            # Generar nombre único
            lower = archivo.name.lower()
            if lower.endswith('.bil.hdr'):
                ext = '.bil.hdr'
            elif lower.endswith('.bil'):
                ext = '.bil'
            else:
                ext = os.path.splitext(archivo.name)[1]

            unique = uuid.uuid4().hex
            nombre_almac = f"{prefijo}{unique}{ext}"
            ruta = os.path.join("archivos_subidos", nombre_almac)

            # Guardar en disco
            with open(ruta, "wb") as f:
                f.write(archivo.read())

            # Identificar rutas
            if ext == '.bil.hdr':
                hdr_file = ruta
            elif ext == '.bil':
                bil_file = ruta
                nombre_base = base  # para mostrar al usuario
                st.markdown(
                    f"""
                    <div style="background:#303030;padding:8px;border-radius:5px;margin-bottom:6px;">
                        <span style="color:#a5d6a7;font-weight:600;">
                            Archivo cargado: {prefijo}{base}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    return hdr_file, bil_file, nombre_base
                

    return hdr_file, bil_file, nombre_base
