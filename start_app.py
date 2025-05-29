import subprocess
import time
import webbrowser
import os
import signal
import platform

def main():
    try:
        print("🚀 Iniciando backend FastAPI...")
        backend_process = subprocess.Popen(
            ["uvicorn", "backend.main:app", "--port", "8000"],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0
        )

        time.sleep(2)

        print("🧠 Iniciando frontend Streamlit...")
        frontend_process = subprocess.Popen(
            ["streamlit", "run", "frontend/app.py"],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0
        )

        time.sleep(3)
        webbrowser.open("http://localhost:8501")

        frontend_process.wait()
        print("🛑 Cerrando backend...")
        backend_process.terminate()

    except KeyboardInterrupt:
        print("🛑 Interrumpido por usuario. Cerrando procesos...")
        backend_process.terminate()
        frontend_process.terminate()

if __name__ == "__main__":
    main()