import streamlit as st
from PIL import Image

# Inicializar sesión
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


#función para los videos

import subprocess
import os

def convertir_a_h264(video_path):
    """
    Convierte un vídeo MP4 al codec H.264 si no existe una versión '_h264'.
    Devuelve la ruta al archivo compatible.
    """
    if not video_path.endswith(".mp4"):
        return video_path

    dir_path, filename = os.path.split(video_path)
    base, _ = os.path.splitext(filename)
    output_filename = f"{base}_h264.mp4"
    output_path = os.path.join(dir_path, output_filename)

    if os.path.exists(output_path):
        return output_path  # Ya está convertido

    try:
        # Ejecutar ffmpeg para convertir el video
        cmd = [
            "ffmpeg",
            "-y",  # overwrite sin preguntar
            "-i", video_path,
            "-vcodec", "libx264",
            "-acodec", "aac",
            "-strict", "experimental",
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path
    except Exception as e:
        st.error(f"Error al convertir el vídeo: {e}")
        return None


# Función para login
def login():
    st.title("Iniciar sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    
    if "login_failed" not in st.session_state:
        st.session_state.login_failed = False

    if st.button("Iniciar sesión"):
        if username == "admin" and password == "ONSL":
            st.session_state.logged_in = True
            st.session_state.login_failed = False
        else:
            st.session_state.login_failed = True

    if st.session_state.login_failed:
        st.error("Usuario o contraseña incorrectos")

# Función para logout
def logout():
    st.session_state.logged_in = False
    st.success("Sesión cerrada correctamente")
    st.stop()

# Función para página principal
def home():
    st.title("Demo | Monitoreo de uso de EPIs")
    video_path = convertir_a_h264("BACKEND/archivos/DETECCION_EPIS_EJEMPLO_corto.mp4")
    if video_path:
        st.video(video_path, format="video/mp4", loop=True, autoplay=True, muted=True)

# Función para tutorial
def tutorial():
    st.title("Tutorial")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Acerca de la API")
        st.write("Desarrollado por Oesía Networks...")
    with col2:
        video_path = convertir_a_h264("BACKEND/archivos/DETECCION_EPIS_EJEMPLO_corto.mp4")
        if video_path:
            st.video(video_path, loop=True, autoplay=True, muted=True)

    st.subheader("¿Cómo funciona?")
    st.write("El usuario puede subir imágenes, vídeos...")


# Si no ha iniciado sesión, mostrar login
if not st.session_state.logged_in:
    login()
else:
    # Páginas
    home_page = st.Page(home, title="Página principal", icon=":material/home:", default=True)
    tutorial_page = st.Page(tutorial, title="Tutorial", icon=":material/info:")
    logout_page = st.Page(logout, title="Cerrar sesión", icon=":material/logout:")

    
    dashboard = st.Page("paginas/reports/dashboard.py", title="Dashboard", icon=":material/dashboard:")
    bugs = st.Page("paginas/reports/bugs.py", title="Bug reports", icon=":material/bug_report:")
    alerts = st.Page("paginas/reports/alerts.py", title="System alerts", icon=":material/notification_important:")

    search = st.Page("paginas/tools/search.py", title="Search", icon=":material/search:")
    history = st.Page("paginas/tools/history.py", title="History", icon=":material/history:")

    imagen = st.Page("paginas/metodo/imagen.py", title="Imagen", icon=":material/photo_camera:")
    video = st.Page("paginas/metodo/video.py", title="Video", icon=":material/movie:")
    directo = st.Page("paginas/metodo/directo.py", title="Directo", icon=":material/videocam:")

    # Estilos y navegación
    st.markdown(
        """
        <style>
            div[data-testid="stSidebarHeader"] > img, div[data-testid="collapsedControl"] > img {
                height: auto;
                width: 18rem;
            }
            div[data-testid="stSidebarHeader"], div[data-testid="stSidebarHeader"] > *,
            div[data-testid="collapsedControl"], div[data-testid="collapsedControl"] > * {
                display: flex;
                align-items: center;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.logo("BACKEND/archivos/logo.png")

    pg = st.navigation(
        {
            "Inicio": [home_page, tutorial_page],
            "Métodos": [imagen, video, directo],
            "Herramientas": [bugs, alerts],
            "Cuenta": [logout_page]
        }
    )

    pg.run()