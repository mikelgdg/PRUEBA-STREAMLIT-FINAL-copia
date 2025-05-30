import subprocess
import time
import webbrowser
import os
import tempfile
import threading

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def get_resource_path(relative_path):
    """Devuelve la ruta absoluta para recursos, compatible con PyInstaller (.exe)"""
    if getattr(sys, 'frozen', False):  # Si es ejecutado desde un .exe
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def stream_output(process, name):
    """Lee y muestra la salida de un subproceso en tiempo real (modo binario robusto)"""
    for line in iter(process.stdout.readline, b''):
        print(f"[{name}] {line.decode('utf-8', errors='replace').rstrip()}")
    process.stdout.close()


def watch_for_exit(backend, frontend):
    try:
        while True:
            cmd = input("\nEscribe 'q' para salir: ").strip().lower()
            if cmd in ("q", "exit"):
                print("🛑 Cerrando aplicaciones...")
                frontend.terminate()
                backend.terminate()
                break
    except KeyboardInterrupt:
        print("\n🛑 Interrupción detectada. Cerrando aplicaciones...")
        frontend.terminate()
        backend.terminate()




if __name__ == "__main__":
    os.environ["STREAMLIT_RUN_ON_SAVE"] = "false"

    backend_path = get_resource_path("BACKEND/app.py")
    frontend_path = get_resource_path("FRONTEND/streamlit_app.py")

    # Lanzar el backend con Uvicorn
    backend = subprocess.Popen(
    [sys.executable, "-u", "-m", "uvicorn", "BACKEND.app:app", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT
)


    threading.Thread(target=stream_output, args=(backend, "BACKEND"), daemon=True).start()

    time.sleep(2)

    # Abrir navegador solo una vez
    flag_file = os.path.join(tempfile.gettempdir(), "streamlit_browser_opened.flag")
    url = "http://localhost:8501"

    if not os.path.exists(flag_file):
        webbrowser.open(url)
        with open(flag_file, "w") as f:
            f.write("opened")

    # Lanzar Streamlit
    frontend = subprocess.Popen(
    [sys.executable, "-u", "-m", "streamlit", "run", frontend_path, "--server.runOnSave=false"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT
)

    threading.Thread(target=stream_output, args=(frontend, "FRONTEND"), daemon=True).start()

    # Hilo para escuchar comandos de salida del usuario
    threading.Thread(target=watch_for_exit, args=(backend, frontend), daemon=True).start()





    # Esperar a que el frontend termine
    frontend.wait()
    backend.terminate()

    # Eliminar el flag al salir
    if os.path.exists(flag_file):
        os.remove(flag_file)
