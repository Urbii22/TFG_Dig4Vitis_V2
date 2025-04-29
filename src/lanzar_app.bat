@echo off
REM -- Sitúate en la carpeta donde reside este .bat:
cd /d "%~dp0"

REM -- Lanza tu app Streamlit (main.py en la misma carpeta)
streamlit run main.py

REM -- (Opcional) Mantiene la ventana abierta tras cerrar Streamlit
pause
