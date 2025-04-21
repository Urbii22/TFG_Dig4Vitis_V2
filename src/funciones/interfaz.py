import streamlit as st
import streamlit.components.v1 as components

def cargar_video():
    st.markdown("<h2 style='text-align: center;'>Evaluación en tiempo real</h2>", unsafe_allow_html=True)

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
        width: 400px;   /* Ajusta a tu preferencia */
        height: 300px;  /* Ajusta a tu preferencia */
        border: 1px solid #ccc;
        object-fit: cover; /* Para recortar la imagen si la relación de aspecto no coincide exactamente */
      }
      button {
        margin-top: 10px;
        padding: 10px 20px;
        font-size: 16px;
        cursor: pointer;
      }
    </style>
    </head>
    <body>
    <div class="container">
      <!-- Columna Izquierda: Streaming de la webcam -->
      <div class="column">
        <video id="video" autoplay playsinline></video>
        <br>
        <button id="captureButton">Capturar foto</button>
      </div>

      <!-- Columna Derecha: Imagen capturada y botón para Guardar -->
      <div class="column">
        <img id="capturedImage" src="" alt="Imagen capturada" />
        <br>
        <button id="saveButton">Guardar foto</button>
      </div>
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

      // --- CAPTURAR IMAGEN ---
      const captureButton = document.getElementById('captureButton');
      captureButton.addEventListener('click', function(){
          const canvas = document.createElement('canvas');
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const context = canvas.getContext('2d');
          context.drawImage(video, 0, 0, canvas.width, canvas.height);
          const dataURL = canvas.toDataURL('image/png');
          document.getElementById('capturedImage').src = dataURL;
      });

      // --- GUARDAR IMAGEN ---
      const saveButton = document.getElementById('saveButton');
      saveButton.addEventListener('click', function(){
          const capturedImage = document.getElementById('capturedImage');
          if (capturedImage.src && capturedImage.src.trim() !== "") {
              // Creamos un enlace temporal para forzar la descarga de la imagen
              const link = document.createElement('a');
              link.href = capturedImage.src;
              link.download = 'captura.png';
              link.click();
          } else {
              alert('No hay ninguna imagen capturada para guardar.');
          }
      });
    </script>
    </body>
    </html>
    """

    # Insertar el HTML dentro de la app. Ajusta el 'height' según te convenga.
    components.html(html_code, height=600)



