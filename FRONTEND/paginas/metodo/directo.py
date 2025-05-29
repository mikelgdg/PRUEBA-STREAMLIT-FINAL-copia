import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import cv2
import tempfile
import json
import requests
import os

dibujo_hecho = False
json_subido = False
informee = ""
BACKEND_URL = "http://localhost:8000"
clases_seleccionadas = []
zona_json = []
zona_canvas = []
incumplimientos = []

# --- Estado de la cámara en sesión ---
if "camara_activa" not in st.session_state:
    st.session_state.camara_activa = False

# --- CONTENEDOR SUPERIOR ---
with st.container():
    col1, space, col2 = st.columns([1.5, 0.1, 0.8])

    with col2:
        st.subheader("Parámetros")
        st.markdown("Detección en zonas:")
        options = ["Activa", "Inactiva"]
        selection = st.pills(" ", options, selection_mode="single", label_visibility="collapsed")
        st.session_state.selection = selection

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

    with space:
        st.markdown('''
            <div style="display: flex; justify-content: center;">
                <div class="divider-vertical-line"></div>
            </div>
            <style>
                .divider-vertical-line {
                    border-left: 1px solid rgba(49, 51, 63, 0.2);
                    height: 270px;
                }
            </style>
        ''', unsafe_allow_html=True)

    with col1:
        st.header("Inferencia en directo")
        with st.expander("Cómo utilizar este método"):
            st.write('''
                1. Ajusta los parámetros
                2. Si zonas está inactiva, abre la cámara y detecta en tiempo real
                3. Si zonas está activa, captura un fotograma y dibuja zonas sobre él
            ''')

        stframe = st.empty()
        frame = None

        if selection == "Inactiva":
            if not st.session_state.camara_activa:
                if st.button("📸 Activar cámara en vivo"):
                    st.session_state.camara_activa = True
                    st.rerun()
            else:
                st.info("Cámara en vivo activada. Pulsa 'Detener cámara' para parar el streaming.")
                clases_param = ",".join(clases_seleccionadas)
                st.markdown(
                    f'<img src="{BACKEND_URL}/video_feed/?clases={clases_param}" width="100%">',
                    unsafe_allow_html=True
                )
                if st.button("Detener cámara"):
                    st.session_state.camara_activa = False
                    st.rerun()

        elif selection == "Activa":
            if "camara_abierta" not in st.session_state:
                st.session_state.camara_abierta = False

            abrir = st.button("Abrir cámara")
            capturar = st.button("📸 Capturar fotograma", disabled=not st.session_state.camara_abierta)
            cerrar = st.button("Cerrar cámara", disabled=not st.session_state.camara_abierta)

            if abrir:
                st.session_state.camara_abierta = True
                st.session_state.frame = None
                st.rerun()
            if cerrar:
                st.session_state.camara_abierta = False
                st.rerun()

            if st.session_state.camara_abierta:
                cap = cv2.VideoCapture(0)
                while st.session_state.camara_abierta:
                    ret, image_np = cap.read()
                    if not ret:
                        st.warning("No se pudo capturar imagen.")
                        break
                    image_np = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
                    frame = Image.fromarray(image_np)
                    stframe.image(frame, caption="Vista previa de la cámara", use_container_width=True)
                    if capturar:
                        st.session_state.frame = frame
                        st.session_state.camara_abierta = False
                        stframe.image(frame, caption="Fotograma capturado", use_container_width=True)
                        break
                cap.release()
            elif "frame" in st.session_state and st.session_state.frame is not None:
                stframe.image(st.session_state.frame, caption="Fotograma capturado", use_container_width=True)

# --- DIBUJO DE ZONAS ---
if (
    selection == "Activa"
    and not st.session_state.get("camara_abierta", False)
    and "frame" in st.session_state
    and st.session_state.frame is not None
):
    st.divider()
    with st.container():
        st.subheader("Determina las zonas de detección a continuación:")

        col_canvas1, spaceee, col_canvas2 = st.columns([0.8, 0.1, 1.5])

        with col_canvas2:
            st.write("... o sube un json con sus coordenadas.")
            uploaded_json = st.file_uploader(" ", label_visibility="collapsed", type=["json"], key="json_directo")
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

        with col_canvas1:
            st.write("Dibuja la zona sobre la imagen...")
            resized_image = st.session_state.frame.resize((220, 220), resample=Image.Resampling.LANCZOS)

            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 0, 0.2)",
                stroke_width=2,
                stroke_color="#FFFF00",
                background_image=resized_image,
                update_streamlit=True,
                height=220,
                width=220,
                drawing_mode="polygon",
                key="canvas_directo",
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

# --- RESULTADOS ---
mostrar_resultados = False
if "frame" in st.session_state and st.session_state.frame is not None:
    if st.session_state.selection == "Inactiva":
        mostrar_resultados = True
    elif st.session_state.selection == "Activa" and (json_subido or dibujo_hecho):
        mostrar_resultados = True

if mostrar_resultados:
    st.divider()
    with st.container():
        st.subheader("Resultados de la inferencia")

        clases_param = ",".join(clases_seleccionadas)
        zona_final = zona_json if zona_json else zona_canvas
        zona_encoded = json.dumps(zona_final)

        col1, col2 = st.columns([1.5, 1.5])
        with col1:
            st.markdown("#### Cámara original:")
            

        with col2:
            st.markdown("#### Inferencia en tiempo real:")
            st.markdown(
                f'<img src="{BACKEND_URL}/video_feed/?clases={clases_param}&zona={zona_encoded}" width="100%">',
                unsafe_allow_html=True
            )

        col1, col2 = st.columns([1.5, 1.5])
        with col1:
            st.subheader("Informe de resultados:")
            st.warning("⚠️ El informe solo está disponible en inferencia sobre fotograma.")
        with col2:
            st.subheader("Descargar resultados:")
            st.warning("⚠️ Las descargas están deshabilitadas en inferencia en directo.")