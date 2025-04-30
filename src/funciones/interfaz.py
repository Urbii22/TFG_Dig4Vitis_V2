import streamlit as st
import streamlit.components.v1 as components

def cargar_video():
    

    # Código HTML, CSS y JavaScript para el streaming y la captura/descarga de la imagen
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
      .container {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-around;
        align-items: flex-start; /* Alinea ambas columnas arriba */
      }
      .column {
        flex: 1;
        margin: 10px;
        text-align: center;
      }
      /* Forzamos un tamaño igual en video y en img para mantener la misma altura */
      video, img {
        width: 900px;   /* Ajusta a tu preferencia */
        height: 550px;  /* Ajusta a tu preferencia */
        border: 1px solid #ccc;
        object-fit: cover; /* Para recortar la imagen si la relación de aspecto no coincide exactamente */
      }
      }
    </style>
    </head>
    <body>
    <div class="container">
      <!-- Columna Izquierda: Streaming de la webcam -->
      <div class="column">
        <video id="video" autoplay playsinline></video>
        <br>
      </div>


    <script>
      // --- STREAMING ---
      const video = document.getElementById('video');
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
          .then(function(stream) {
            video.srcObject = stream;
            video.play();
          })
          .catch(function(err) {
            console.error('Error al acceder a la webcam:', err);
            alert('No se pudo acceder a la webcam.');
          });
      } else {
        alert('Tu navegador no soporta el acceso a la webcam.');
      }
    </script>
    </body>
    </html>
    """

    # Insertar el HTML dentro de la app. Ajusta el 'height' según te convenga.
    components.html(html_code, height=600)



