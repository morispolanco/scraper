# app.py

import streamlit as st
import requests
import pandas as pd
import time
import re

# Configuración de la página
st.set_page_config(
    page_title="Buscador de Profesionales",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título de la aplicación
st.title("Buscador de Profesionales por País y Profesión")

# Sidebar para entradas del usuario
st.sidebar.header("Configuración de Búsqueda")

# Entradas del usuario
pais = st.sidebar.text_input("País", "España")
profesion = st.sidebar.text_input("Profesión", "abogados")
max_contactos = st.sidebar.number_input("Número máximo de contactos", min_value=10, max_value=1000, value=500, step=10)
buscar = st.sidebar.button("Buscar")

# Función para realizar búsquedas con la API de Serper
def buscar_profesionales(profesion, pais, start=0):
    """
    Realiza una búsqueda utilizando la API de Serper.

    :param profesion: Profesión a buscar (e.g., "abogados")
    :param pais: País de interés (e.g., "España")
    :param start: Paginación de resultados
    :return: Lista de URLs de directorios o asociaciones
    """
    consulta = f"{profesion} en {pais}"
    headers = {
        "X-API-KEY": st.secrets["serper_api_key"],
        "Content-Type": "application/json"
    }
    data = {
        "q": consulta,
        "start": start  # Paginación si la API lo soporta
    }

    try:
        response = requests.post("https://google.serper.dev/search", headers=headers, json=data)
        response.raise_for_status()
        resultados = response.json().get("organic", [])
        urls = [res.get("link") for res in resultados if res.get("link")]
        return urls
    except requests.exceptions.RequestException as e:
        st.error(f"Error en la solicitud a la API: {e}")
        return []

# Función para extraer información de contacto de una página web sin usar BeautifulSoup
def extraer_contacto(url):
    """
    Extrae información de contacto desde una página web utilizando expresiones regulares.

    :param url: URL de la página a procesar
    :return: Diccionario con la información de contacto
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            st.warning(f"No se pudo acceder a {url} (Status Code: {response.status_code})")
            return {}

        contenido = response.text

        # Buscar correos electrónicos
        correos = re.findall(r'[\w\.-]+@[\w\.-]+', contenido)
        correo = correos[0] if correos else None

        # Si no hay correo, no incluimos el contacto
        if not correo:
            return {}

        # Buscar teléfonos
        telefonos = re.findall(r'(\+\d{1,3}[- ]?)?\d{9,15}', contenido)
        telefono = telefonos[0] if telefonos else None

        # Buscar nombre (por ejemplo, título de la página)
        titulo_match = re.search(r'<title>(.*?)</title>', contenido, re.IGNORECASE | re.DOTALL)
        nombre = titulo_match.group(1).strip() if titulo_match else "Sin título"

        return {
            "Nombre": nombre,
            "Correo Electrónico": correo,
            "Teléfono": telefono,
            "URL": url
        }
    except Exception as e:
        st.warning(f"Error al procesar {url}: {e}")
        return {}

# Función para generar el archivo Excel
def generar_excel(datos, nombre_archivo="profesionales.xlsx"):
    """
    Genera un archivo Excel con los datos proporcionados.

    :param datos: Lista de diccionarios con los datos de los profesionales.
    :param nombre_archivo: Nombre del archivo Excel a generar.
    """
    df = pd.DataFrame(datos)
    df.to_excel(nombre_archivo, index=False)
    st.success(f"Archivo Excel generado: {nombre_archivo}")
    st.download_button(
        label="Descargar Excel",
        data=df.to_excel(index=False).encode('utf-8'),
        file_name=nombre_archivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# Función principal para coordinar la búsqueda y extracción
def main():
    contactos = []
    start = 0
    resultados_por_pagina = 10  # Depende de la API de Serper
    progreso = st.progress(0)
    total_progress = max_contactos / resultados_por_pagina

    with st.spinner("Buscando profesionales..."):
        while len(contactos) < max_contactos:
            urls = buscar_profesionales(profesion, pais, start)
            if not urls:
                st.info("No se obtuvieron más URLs.")
                break

            st.write(f"Procesando {len(urls)} URLs...")
            for url in urls:
                if len(contactos) >= max_contactos:
                    break
                contacto = extraer_contacto(url)
                if contacto and contacto not in contactos:
                    contactos.append(contacto)
                    st.write(f"Contacto agregado: {contacto['Nombre']} - {contacto['Correo Electrónico']}")
                time.sleep(1)  # Respetar el tiempo entre solicitudes

            start += resultados_por_pagina
            progreso.progress(min(int((start / (max_contactos / resultados_por_pagina)) * 100), 100))
            time.sleep(2)  # Respetar el tiempo entre solicitudes de búsqueda

    progreso.empty()

    if contactos:
        st.success(f"Se obtuvieron {len(contactos)} contactos con correo electrónico.")
        df = pd.DataFrame(contactos)
        st.dataframe(df)

        generar_excel(contactos)
    else:
        st.warning("No se encontraron contactos con correo electrónico.")

# Ejecutar la función principal cuando se apriete el botón
if buscar:
    main()
