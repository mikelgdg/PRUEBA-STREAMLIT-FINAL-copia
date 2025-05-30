import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import tempfile
import cv2
import json
import requests
import subprocess
import os
import time


dibujo_hecho = False
json_subido = False
zona_json = []
zona_canvas = []
incumplimientos = []

BACKEND_URL = "http://localhost:8000"
clases_seleccionadas = []

carpeta_resultados = "salidas"
carpeta_subidas = "subidas"

import shutil
import os

def limpiar_carpeta(nombre_carpeta):
    try:
        if os.path.exists(nombre_carpeta):
            for archivo in os.listdir(nombre_carpeta):
                archivo_path = os.path.join(nombre_carpeta, archivo)
                if os.path.isfile(archivo_path) or os.path.islink(archivo_path):
                    os.unlink(archivo_path)
                elif os.path.isdir(archivo_path):
                    shutil.rmtree(archivo_path)
            print(f"Carpeta '{nombre_carpeta}' limpiada correctamente.")
        else:
            print(f"La carpeta '{nombre_carpeta}' no existe.")
    except Exception as e:
        print(f"Error al limpiar la carpeta '{nombre_carpeta}': {e}")



    
import os
import subprocess

import os
import subprocess
import platform
import glob

def get_ffmpeg_path():
    if platform.system() == "Windows":
        # Ruta relativa al ffmpeg.exe si lo incluyes en tu proyecto
        posible_ruta = os.path.join("ffmpeg", "ffmpeg.exe")
        if os.path.exists(posible_ruta):
            return posible_ruta
        else:
            return "ffmpeg"  # Requiere que esté en el PATH
    else:
        return "ffmpeg"  # macOS/Linux

def montar_video_desde_frames(carpeta_frames, nombre_output="video_resultado.mp4", fps=4):
    output_path = os.path.join(carpeta_frames, nombre_output)
    print(f"Output path: {output_path}")
    
    if os.path.exists(output_path):
        os.remove(output_path)
        print(f"Eliminado archivo existente: {output_path}")

    # Verifica si hay frames antes de correr ffmpeg
    frames = glob.glob(os.path.join(carpeta_frames, "frame_proc_*.jpg"))
    if not frames:
        print("❌ No se encontraron frames para generar el video.")
        return None

    try:
        input_pattern = os.path.join(carpeta_frames, "frame_proc_%04d.jpg")
        print(f"Input pattern: {input_pattern}")

        ffmpeg_cmd = get_ffmpeg_path()

        result = subprocess.run([
            ffmpeg_cmd, "-y",
            "-framerate", str(fps),
            "-i", input_pattern,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            output_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        print("STDOUT:\n", result.stdout)
        print("STDERR:\n", result.stderr)

        if result.returncode != 0:
            print(f"Error al ejecutar ffmpeg (code {result.returncode})")
            return None

        print(f"Video creado correctamente en: {output_path}")
        return output_path

    except Exception as e:
        print(f"Error general: {e}")
        return None


    

def convertir_a_h264(video_input_path):

    ffmpeg_cmd = get_ffmpeg_path()
    output_path = video_input_path.replace(".mp4", "_h264.mp4")
    if os.path.exists(output_path):
         os.remove(output_path)
    try:
        subprocess.run([
            ffmpeg_cmd, "-y",
            "-i", video_input_path,
            "-vcodec", "libx264",
            "-acodec", "aac",
            "-strict", "experimental",
            output_path
        ], check=True)
        return output_path
    except Exception as e:
        st.error(f"Error al convertir a H.264: {e}")
        return video_input_path
    


with st.container():
    col1, space, col2 = st.columns([1.5, 0.1, 0.8])

    with col1:
        st.header("Inferencia en videos")
        with st.expander("Cómo utilizar este método"):
            st.write('''
                1. Ajusta los parámetros
                2. Sube un video a analizar (.mp4 recomendado)
                3. Puedes dibujar una zona de detección o subir un archivo .json
                4. Se mostrará un fotograma representativo y los resultados
            ''')

        uploaded_file = st.file_uploader(" ", label_visibility="collapsed", type=["mp4", "avi", "mov"])
        frame = None
        if uploaded_file is not None:
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tfile.write(uploaded_file.read())
            tfile.flush()
            tfile_path = tfile.name
            cap = cv2.VideoCapture(tfile_path)
            success, image_np = cap.read()
            if success:
                image_np = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
                frame = Image.fromarray(image_np)

    with space:
        st.markdown('''
            <div style="display: flex; justify-content: center;">
                <div class="divider-vertical-line"></div>
            </div>
            <style>
                .divider-vertical-line {
                    border-left: 1px solid rgba(49, 51, 63, 0.2);
                    height: 375px;
                }
            </style>
        ''', unsafe_allow_html=True)

    with col2:
        st.subheader("Parámetros")
        st.markdown("Detección en zonas:")
        options = ["Activa", "Inactiva"]
        selection = st.pills(" ", options, selection_mode="single", label_visibility="collapsed")
        st.session_state.selection = selection

        st.markdown("Clases detectadas:")
        coll1, coll2 = st.columns(2)
        with coll1:
            if st.checkbox("Gafas"):
                clases_seleccionadas.append("Gafas")
            if st.checkbox("Guantes"):
                clases_seleccionadas.append("Guantes")
        with coll2:
            if st.checkbox("Chaleco"):
                clases_seleccionadas.append("Chaleco")
            if st.checkbox("Casco"):
                clases_seleccionadas.append("Casco")

if 'selection' in st.session_state and st.session_state.selection == "Activa" and frame is not None:
    st.divider()
    with st.container():
        st.subheader("Determina las zonas de detección a continuación:")
        col_canvas1, spaceee, col_canvas2 = st.columns([0.8, 0.1, 1.5])

        with col_canvas2:
            st.write("Sube un JSON con coordenadas de la zona...")
            uploaded_json = st.file_uploader(" ", label_visibility="collapsed", type=["json"], key="json")
            if uploaded_json is not None:
                json_subido = True
                try:
                    zona_data = json.load(uploaded_json)
                    objects = zona_data.get("objects", [])
                    for obj in objects:
                        if obj.get("type") == "path":
                            coords = [(cmd[1] / 220, 1 - (220 - cmd[2]) / 220) for cmd in obj["path"] if cmd[0] in ("M", "L")]
                            if len(coords) >= 3:
                                zona_json.append(coords)
                    if zona_json:
                        dibujo_hecho = True
                except Exception as e:
                    st.error(f"❌ Error al cargar el JSON: {e}")
                    zona_json = []

        with spaceee:
            st.markdown('''
                <div style="display: flex; justify-content: center;">
                    <div class="divider-vertical-line"></div>
                </div>
                <style>
                    .divider-vertical-line {
                        border-left: 1px solid rgba(49, 51, 63, 0.2);
                        height: 300px;
                    </style>
            ''', unsafe_allow_html=True)

        with col_canvas1:
            st.write("...o dibújala sobre el fotograma.")
            resized_frame = frame.resize((220, 220), resample=Image.Resampling.LANCZOS)
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 0, 0.2)",
                stroke_width=2,
                stroke_color="#FFFF00",
                background_image=resized_frame,
                update_streamlit=True,
                height=220,
                width=220,
                drawing_mode="polygon",
                key="canvas_video",
                display_toolbar=False
            )
            if canvas_result.json_data is not None and len(canvas_result.json_data["objects"]) > 0:
                dibujo_hecho = True
                objects = canvas_result.json_data.get("objects", [])
                for obj in objects:
                    if obj.get("type") == "path":
                        coords = [(cmd[1] / 220, 1 - (220 - cmd[2]) / 220) for cmd in obj["path"] if cmd[0] in ("M", "L")]
                        if len(coords) >= 3:
                            zona_canvas.append(coords)

            

mostrar_resultados = False
if uploaded_file is not None:
    if st.session_state.selection == "Inactiva":
        mostrar_resultados = True
    elif st.session_state.selection == "Activa" and (json_subido or dibujo_hecho):
        mostrar_resultados = True

if mostrar_resultados:
    st.divider()
    with st.container():
        st.subheader("Resultados de la inferencia")

        video_mostrable = convertir_a_h264(tfile_path)

        col1, col2 = st.columns([1.5, 1.5])
        with col1:
            st.video(video_mostrable, format="video/mp4", loop=True, autoplay=True, muted=True)
            st.write("Video original")

        with col2:
            try:
                _, ext = os.path.splitext(uploaded_file.name)
                ext = ext.lower()
                uploaded_file_bytes = uploaded_file.getvalue()  # Esto es más seguro en Streamlit
                files = {"file": (uploaded_file.name, uploaded_file_bytes, uploaded_file.type)}
                # ✅ Seleccionar la zona válida si existe
                zona_final = zona_json if zona_json else zona_canvas
                data_envio = {
                    "clases": json.dumps(clases_seleccionadas),
                    "zona": json.dumps(zona_final)
                }

                response = requests.post(
                    f"{BACKEND_URL}/upload/",
                    files=files,
                    data=data_envio,
                    timeout=60
                )

                if response.status_code == 200:
                    data = response.json()
                    print(f"Response data: {data}")
                    data_informe_completa = data.get("data_informe_completa", [])
            
                    zona_final = zona_json if zona_json else zona_canvas

                    if "nombre_resultado" in data:
                        nombre = data["nombre_resultado"]
                        url = f"{BACKEND_URL}/salidas/{nombre}"
                        st.video(url, use_container_width=True, format="video/mp4", loop=True, autoplay=True, muted=True)
                        st.write("Resultado de la inferencia")

                    elif "frames_resultados" in data and "carpeta_resultados" in data:
                        carpeta_frames = data["carpeta_resultados"]
                        print(f"Carpeta de frames: {carpeta_frames}")
                        video_path = montar_video_desde_frames(carpeta_frames)
                        print(f"Video path: {video_path}")
                        
                        if video_path:
                            video_resultado = convertir_a_h264(video_path)
                            st.video(video_resultado, format="video/mp4", loop=True, autoplay=True, muted=True)
                            st.write("Resultado de la inferencia")
                        else:
                            st.error("❌ No se pudo generar el video de resultados.")
                    else:
                        st.warning("⚠️ El servidor no devolvió un resultado de video esperado.")

                    limpiar_carpeta(carpeta_subidas)
                    #limpiar_carpeta(carpeta_resultados)

            except Exception as e:
                st.error(f"❌ Error inesperado: {e}")

        col1, col2 = st.columns([1.5, 1.5])
        with col1:
            mensaje_informe = ""
            st.subheader("Informe de resultados:")
            #print(f"Data informe completa: {data_informe_completa}")
            if data_informe_completa:
                for frame in data_informe_completa:
                    for item in frame:
                        mensaje_informe += f"{item};"
                    mensaje_informe += "\n"
                st.error(mensaje_informe)
            else:
                mensaje_informe = "No se han detectado anomalías en el video."
                st.success(mensaje_informe)
            informe_txt = mensaje_informe.encode("utf-8")

        with col2:
            st.subheader("Descargar resultados:")
            options = ["Fotograma", "JSON zona dibujada", "Informe"]
            selection = st.segmented_control(" ", options, selection_mode="single", label_visibility="collapsed")

            if selection == "Fotograma":
                buf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                frame.save(buf.name)
                with open(buf.name, "rb") as f:
                    st.download_button("Descargar fotograma", data=f, file_name="fotograma.png", mime="image/png")

            elif selection == "JSON zona dibujada":
                if dibujo_hecho:
                    st.download_button(
                        label="Descargar JSON",
                        data=json.dumps(canvas_result.json_data, indent=2),
                        file_name="zona_dibujada.json",
                        mime="application/json"
                    )
                else:
                    st.info("No hay zona dibujada para descargar.")

            elif selection == "Informe":
                st.download_button(
                    label="Descargar informe",
                    data=informe_txt,
                    file_name="informe.txt",
                    mime="text/plain"
                )