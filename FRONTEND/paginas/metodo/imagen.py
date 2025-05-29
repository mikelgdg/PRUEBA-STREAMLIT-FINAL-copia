import streamlit as st
from streamlit_drawable_canvas import st_canvas

from PIL import Image
import time
import json
import requests
import os

dibujo_hecho = False
json_subido = False  # ✅ NUEVO


BACKEND_URL = "http://localhost:8000"

clases_seleccionadas = []
# Evita errores por variables no definidas
zona_json = []
zona_canvas = []
incumplimientos=[]

carpeta_subidas= "subidas"
carpeta_resultados= "salidas"


def limpiar_carpeta(nombre_carpeta):
    try:
        if os.path.exists(nombre_carpeta):
            for archivo in os.listdir(nombre_carpeta):
                archivo_path = os.path.join(nombre_carpeta, archivo)
                if os.path.isfile(archivo_path) or os.path.islink(archivo_path):
                    os.unlink(archivo_path)
                elif os.path.isdir(archivo_path):
                    shutil.rmtree(archivo_path)
            print(f"🧹 Carpeta '{nombre_carpeta}' limpiada correctamente.")
        else:
            print(f"📁 La carpeta '{nombre_carpeta}' no existe.")
    except Exception as e:
        print(f"❌ Error al limpiar la carpeta '{nombre_carpeta}': {e}")

limpiar_carpeta(carpeta_resultados)

# --- CONTENEDOR SUPERIOR ---
print("INICIO DE LA PÁGINA DE IMÁGENES")
with st.container():
    col1, space, col2 = st.columns([1.5, 0.1, 0.8])

    with col1:
        st.header("Inferencia en imágenes")
        with st.expander("Cómo utilizar este método"):
            st.write('''
                1. Ajusta los parámetros
                2. Selecciona la imagen a analizar
                3. La comparación de imágenes se mostrará a continuación. Puede descargarla haciendo clic en el botón de descarga.
            ''')
        uploaded_file = st.file_uploader(" ", label_visibility="collapsed", type=["jpg", "jpeg", "png"])
        image = None
        if uploaded_file is not None:
            image = Image.open(uploaded_file)

    with space:
        st.markdown(
            '''
            <div style="display: flex; justify-content: center;">
                <div class="divider-vertical-line"></div>
            </div>
            <style>
                .divider-vertical-line {
                    border-left: 1px solid rgba(49, 51, 63, 0.2);
                    height: 270px;
                }
            </style>
            ''',
            unsafe_allow_html=True
        )

    with col2:
        st.subheader("Parámetros")

        st.markdown("Detección en zonas:")
        options = ["Activa", "Inactiva"]
        selection = st.pills(" ", options, selection_mode="single", label_visibility="collapsed")
        st.session_state.selection = selection  # Guardar en estado

        st.markdown("Clases detectadas:")
        coll1, coll2 = st.columns(2)
        with coll1:
            gafas = st.checkbox("Gafas")
            if gafas:
                clases_seleccionadas.append("Gafas")
            guantes = st.checkbox("Guantes")
            if guantes:
                clases_seleccionadas.append("Guantes")
        with coll2:
            chaleco = st.checkbox("Chaleco")
            if chaleco:
                clases_seleccionadas.append("Chaleco")
            casco = st.checkbox("Casco")
            if casco:
                clases_seleccionadas.append("Casco")

        #st.markdown("Confianza:")
        #confianza = st.slider("Confianza:", 0, 50, 100, label_visibility="collapsed")

# --- NUEVO CONTENEDOR: SOLO SI SELECCIÓN ES ACTIVA ---
if 'selection' in st.session_state and st.session_state.selection == "Activa" and uploaded_file is not None:
    st.divider()
    with st.container():
        st.subheader("Determina las zonas de detección a continuación:")

        col_canvas1, spaceee, col_canvas2 = st.columns([0.8, 0.1, 1.5])

        zona_json = []     # ✅ Zona cargada desde archivo JSON
        zona_canvas = []   # ✅ Zona dibujada manualmente
        dibujo_hecho = False
        json_subido = False

        # --- CARGA DESDE JSON ---
        with col_canvas2:
            st.write("... o sube un json con sus coordenadas.")
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
                            else:
                                st.info("Dibuja al menos 3 puntos para formar el polígono.")
                    if zona_json:
                        dibujo_hecho = True
                        #st.success("Zona guardada exitosamente.")
                        #st.write(zona_json[-1])
                except Exception as e:
                    st.error(f"❌ Error al cargar el JSON: {e}")
                    zona_json = []

        # --- DIVISOR VERTICAL ESTÉTICO ---
        with spaceee:
            st.markdown(
                '''
                <div style="display: flex; justify-content: center;">
                    <div class="divider-vertical-line"></div>
                </div>
                <style>
                    .divider-vertical-line {
                        border-left: 1px solid rgba(49, 51, 63, 0.2);
                        height: 300px;
                    }
                </style>
                ''',
                unsafe_allow_html=True
            )

        # --- DIBUJO MANUAL CON ST_CANVAS ---
        with col_canvas1:
            st.write("Dibuja la zona sobre la imagen...")
            resized_image = image.resize((220, 220), resample=Image.Resampling.LANCZOS)

            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 0, 0.2)",
                stroke_width=2,
                stroke_color="#FFFF00",
                background_image=resized_image,
                update_streamlit=True,
                height=220,
                width=220,
                drawing_mode="polygon",
                key="canvas_mini",
                display_toolbar=True
            )

            if canvas_result.json_data is not None and len(canvas_result.json_data["objects"]) > 0:
                dibujo_hecho = True
                objects = canvas_result.json_data.get("objects", [])
                for obj in objects:
                    if obj.get("type") == "path":
                        coords = [(cmd[1] / 220, 1 - (220 - cmd[2]) / 220) for cmd in obj["path"] if cmd[0] in ("M", "L")]
                        if len(coords) >= 3:
                            zona_canvas.append(coords)

# --- CONTENEDOR DE RESULTADOS ---
mostrar_resultados = False
data_informe = []
mensaje_informe = ""
nombre = None  # También es importante inicializar esto

if uploaded_file is not None:
    if st.session_state.selection == "Inactiva":
        mostrar_resultados = True
    elif st.session_state.selection == "Activa" and (json_subido or dibujo_hecho):
        mostrar_resultados = True

if mostrar_resultados:
    st.divider()
    with st.container():
        st.subheader("Resultados de la inferencia")

        col1, col2 = st.columns([1.5, 1.5])

        with col1:
            st.image(image, caption="Imagen original", use_container_width=True)

        

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
                    if ext in [".jpg", ".jpeg", ".png"]:
                        nombre = data.get("nombre_resultado")
                        data_informe = data.get("data_informe", [])
                        timestamp = data.get("timestamp", time.strftime("%Y-%m-%d_%H:%M:%S"))
                        #print("Data Informe: ", data_informe)
                        #print("Timestamp: ", timestamp)

                        if nombre:
                            url = f"{BACKEND_URL}/salidas/{nombre}"
                            st.image(url, caption="Resultado de la inferencia", use_container_width=True)
                            limpiar_carpeta(carpeta_subidas)
                    else:
                        print(response.status_code)
                else:
                    st.error(f"❌ Error del servidor: {response.status_code}")
                    print(response.text)
            except Exception as e:
                st.error(f"❌ Error inesperado: {e}")

        col1, col2 = st.columns([1.5, 1.5])
        with col1:
            st.subheader("Informe de resultados:")
            mensaje_informe = ""

            if data_informe:
                for item in data_informe:
                    for i in item:
                        mensaje_informe += f"{i};"
                    mensaje_informe += "\n"
                    
                
            else:
                mensaje_informe = "No se han detectado anomalías en la imagen."
                st.success(mensaje_informe)

            # Guardar el informe como string codificado para la descarga
            informe_txt = mensaje_informe.encode("utf-8")

        with col2:
            options = ["Resultado", "JSON zona dibujada", "Informe"]
            st.subheader("Descargar resultados:")

            selection = st.segmented_control(" ", options, selection_mode="single", label_visibility="collapsed")

            if selection == "Resultado":
                if nombre:
                    try:
                        resultado_url = f"{BACKEND_URL}/salidas/{nombre}"
                        resultado_response = requests.get(resultado_url)
                        if resultado_response.status_code == 200:
                            st.download_button(
                                label="Descargar resultado",
                                data=resultado_response.content,
                                file_name="resultado_inferencia.png",
                                mime="image/png"
                            )
                        else:
                            st.error("No se pudo descargar el resultado del backend.")
                    except Exception as e:
                        st.error(f"❌ Error al obtener la imagen de resultado: {e}")
                else:
                    st.warning("No hay resultado disponible para descargar.")

            elif selection == "JSON zona dibujada":
                if dibujo_hecho==True:
                    st.download_button(
                        label="Descargar json",
                        data=json.dumps(canvas_result.json_data, indent=2),
                        file_name="zona_dibujada.json",
                        mime="application/json"
                    )
                else:
                    st.warning("No se ha dibujado una zona")

            elif selection == "Informe":
                st.download_button(
                    label="Descargar informe",
                    data=informe_txt,
                    file_name="informe.txt",
                    mime="text/plain"
                )
print("FINAL DE LA PÁGINA DE IMÁGENES")