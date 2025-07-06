<div align="center">
  <img src="https://raw.githubusercontent.com/Urbii22/TFG_Dig4Vitis_V2/interfaz_new/src/recursos/EcoVid_logo.png" alt="EcoVid Logo" width="150"/>
  <h1>🌱 EcoVid: Detección de Cobre en Viñedos con Visión Hiperespectral</h1>
  <p><strong>Análisis de imágenes hiperespectrales para la detección y cuantificación de tratamientos de cobre en hojas de vid.</strong></p>

  <p>
    <a href="https://www.python.org" target="_blank"><img alt="Python" src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python"></a>
    <a href="https://streamlit.io" target="_blank"><img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-1.36-red?style=for-the-badge&logo=streamlit"></a>
    <a href="https://opencv.org" target="_blank"><img alt="OpenCV" src="https://img.shields.io/badge/OpenCV-4.10-blue?style=for-the-badge&logo=opencv"></a>
    <a href="https://github.com/Urbii22/TFG_Dig4Vitis_V2/blob/main/LICENSE" target="_blank"><img alt="Licencia" src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"></a>
  </p>
</div>

---

## 📖 Resumen del Proyecto

**EcoVid** es una herramienta de software, desarrollada como parte de un Trabajo de Fin de Grado, que se enmarca en el área de la **agricultura de precisión**. Su objetivo principal es analizar imágenes hiperespectrales para **detectar y cuantificar con precisión la cobertura de tratamientos antifúngicos con base de cobre** en hojas de viñedo.

El sistema utiliza un enfoque innovador de análisis dual: compara una imagen de la hoja **antes del tratamiento** (control) con una imagen **después del tratamiento**. Gracias a avanzados algoritmos de visión por computador, EcoVid es capaz de alinear ambas imágenes a la perfección y **eliminar los falsos positivos** causados por las variaciones naturales de la propia hoja (nervios, brillos), aislando únicamente el producto aplicado.

La aplicación web, construida con **Streamlit**, ofrece una interfaz intuitiva para que investigadores y técnicos puedan obtener un resultado visual inmediato y un porcentaje de recubrimiento exacto, facilitando la optimización de tratamientos y promoviendo una viticultura más sostenible.

---

## ✨ Características Principales

-   **Análisis Hiperespectral Avanzado**: Procesa pares de imágenes en formato ENVI (`.bil` + `.hdr`) para un análisis espectral detallado.
-   **Reducción de Ruido Inteligente**: Implementa un sistema de sustracción de ruido que elimina falsos positivos. ¡Esta es la clave del proyecto!
-   **Alineación Automática de Precisión**: Utiliza los algoritmos **ORB y RANSAC** para alinear geométricamente las imágenes de control y de tratamiento, corrigiendo cualquier desplazamiento o rotación.
-   **Cuantificación Exacta**: Calcula el **porcentaje de recubrimiento** del producto sobre la superficie foliar común, ofreciendo una métrica clara y objetiva.
-   **Interfaz Web Interactiva**: Una aplicación fácil de usar que guía al usuario en todo el proceso: cargar, procesar y analizar.
-   **Resultados Visuales y Descargables**: Muestra una imagen final con el producto resaltado y permite descargar tanto el resultado final como las imágenes de los pasos intermedios para una validación exhaustiva.

---

## 🛠️ Stack Tecnológico

EcoVid ha sido construido utilizando el ecosistema científico de Python, aprovechando bibliotecas de alto rendimiento para el análisis de datos y la visión por computador.

| **Python** | **Streamlit** | **OpenCV** | **NumPy** | **Spectral** | **Pillow** |
|:----------:|:-------------:|:----------:|:---------:|:------------:|:----------:|
| <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" alt="Python Icon" width="40"> | <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/streamlit/streamlit-original.svg" alt="Streamlit Icon" width="40"> | <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/opencv/opencv-original.svg" alt="OpenCV Icon" width="40"> | <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/numpy/numpy-original.svg" alt="NumPy Icon" width="40"> | `SPY` | `PIL` |

---

## ⚙️ ¿Cómo Funciona? Metodología

El núcleo de EcoVid es un pipeline de procesamiento de tres fases, diseñado para garantizar la máxima precisión.

1.  **Trinarización (Segmentación Inicial)**
    El primer paso es segmentar cada imagen para identificar tres clases distintas: el fondo (negro), la hoja (verde) y las posibles detecciones de producto (rojo). Esto se logra aplicando umbrales específicos en las bandas hiperespectrales más relevantes.

2.  **Alineación Automática por ORB y RANSAC**
    Dado que es imposible volver a colocar la hoja exactamente en la misma posición, la alineación es crucial.
    -   Primero, se detectan los **bordes** de la hoja en ambas imágenes.
    -   Luego, el algoritmo **ORB** extrae cientos de puntos característicos de esos bordes y los compara para encontrar coincidencias.
    -   Finalmente, **RANSAC** utiliza las mejores coincidencias para calcular la transformación geométrica exacta (rotación, traslación) que superpone una imagen sobre la otra con una precisión a nivel de subpíxel.

3.  **Sustracción de Ruido y Cálculo Final**
    Con las imágenes perfectamente alineadas, el sistema realiza una sustracción lógica:
    > Un píxel se considera **producto real** si, y solo si, se detecta en la imagen CON tratamiento y **NO** se detecta en la imagen SIN tratamiento.

    Este enfoque diferencial permite eliminar las variaciones de reflectancia naturales de la hoja, que son la principal fuente de error, garantizando que solo se cuantifique el producto aplicado.

---

## 🚀 Puesta en Marcha

Para ejecutar EcoVid en tu máquina local, sigue estos pasos. El método recomendado es usar **Docker** para asegurar un entorno 100% reproducible.

### Método 1: Ejecución con Docker (Recomendado)

1.  **Instala Docker Desktop**: Descárgalo desde la [web oficial de Docker](https://www.docker.com/products/docker-desktop/).

2.  **Clona el repositorio**:
    ```bash
    git clone [https://github.com/Urbii22/TFG_Dig4Vitis_V2.git](https://github.com/Urbii22/TFG_Dig4Vitis_V2.git)
    cd TFG_Dig4Vitis_V2/
    ```

3.  **Construye la imagen de Docker**:
    Este comando creará un contenedor con todas las dependencias necesarias. Puede tardar unos minutos la primera vez.
    ```bash
    docker build -t ecovid-app ./TFG_Dig4Vitis_V2-interfaz_new/src/
    ```

4.  **Ejecuta el contenedor**:
    ```bash
    docker run -p 8501:8501 ecovid-app
    ```

5.  **Abre la aplicación**:
    Abre tu navegador y ve a la dirección [**http://localhost:8501**](http://localhost:8501).

### Método 2: Ejecución Local (con Python)

1.  **Clona el repositorio**:
    ```bash
    git clone [https://github.com/Urbii22/TFG_Dig4Vitis_V2.git](https://github.com/Urbii22/TFG_Dig4Vitis_V2.git)
    cd TFG_Dig4Vitis_V2/TFG_Dig4Vitis_V2-interfaz_new/
    ```

2.  **Crea un entorno virtual (recomendado)**:
    ```bash
    python -m venv venv
    # Actívalo
    # En Windows:
    # venv\Scripts\activate
    # En macOS/Linux:
    # source venv/bin/activate
    ```

3.  **Instala las dependencias**:
    ```bash
    pip install -r src/requirements.txt
    ```

4.  **Ejecuta la aplicación**:
    ```bash
    streamlit run src/main.py
    ```

---

## 🖥️ Uso de la Aplicación

La interfaz web te guiará de forma sencilla:

1.  **Carga de Imágenes SIN Tratamiento**: En el panel izquierdo, arrastra o selecciona los archivos `.bil` y `.hdr` de la hoja de control.
2.  **Carga de Imágenes CON Tratamiento**: En el panel derecho, haz lo mismo para la hoja tratada.
3.  **Iniciar Procesamiento**: Haz clic en el botón "🚀 Iniciar Procesamiento". El sistema analizará las imágenes.
4.  **Analizar Resultados**: La aplicación mostrará la imagen final con el producto detectado en rojo y el porcentaje de cobertura.
5.  **Explorar y Descargar**: Utiliza el desplegable "Ver detalles" para inspeccionar la calidad del alineamiento y descarga las imágenes que necesites para tus informes.

---

## 📂 Estructura del Proyecto

El código está organizado de forma modular para facilitar su mantenimiento y escalabilidad.

```
TFG_Dig4Vitis_V2/
└── TFG_Dig4Vitis_V2-interfaz_new/
    ├── src/
    │   ├── funciones/         # Módulos con la lógica del backend
    │   │   ├── alignment.py   # Algoritmos de alineación (ORB, RANSAC)
    │   │   ├── archivos.py    # Gestión de carga de archivos
    │   │   ├── interfaz.py    # Componentes de la interfaz de usuario
    │   │   └── procesamiento.py # Pipeline de análisis principal
    │   ├── recursos/          # Logos e imágenes de la UI
    │   ├── main.py            # Punto de entrada de la aplicación Streamlit
    │   ├── estilos.css        # Hoja de estilos para la apariencia visual
    │   └── requirements.txt   # Dependencias de Python
    ├── Memoria_TFG.pdf
    └── Anexos_TFG.pdf
```

---

## 📜 Licencia

Este proyecto está distribuido bajo la **Licencia MIT**. Eres libre de usar, modificar y distribuir el código, siempre que se dé crédito al autor original.

---

## 🎓 Agradecimientos

Este proyecto ha sido desarrollado como Trabajo de Fin de Grado para el **Grado en Ingeniería Informática** de la **Escuela Politécnica Superior** de la **Universidad de Burgos**.

-   **Autor**: Diego Urbaneja Portal
-   **Tutores**: Dr. Carlos Cambra Baseca y Dr. Ramón Sánchez Alonso
-   **Grupo de Investigación**: GICAP - Grupo de investigación en Ingeniería de Sistemas Inteligentes y Computación de Altas Prestaciones.

Financiado en el marco del proyecto **Dig4Vitis**.
