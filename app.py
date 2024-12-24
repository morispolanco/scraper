import streamlit as st
import requests
import re
import pandas as pd
from io import BytesIO

# -------------------------------------------------------------
# Función para hacer la búsqueda usando la API de Serper (o la que elijas)
# -------------------------------------------------------------
def search_web(profession, country, api_key, num_results=20):
    """
    Envía una consulta a la API de Serper para buscar sitios relacionados
    con la profesión y el país indicados. Devuelve la lista de URLs
    encontradas (título, snippet, link).
    
    :param profession: str - Profesión a buscar
    :param country: str - País a buscar
    :param api_key: str - Clave de la API Serper
    :param num_results: int - Cantidad de resultados a pedir
    :return: list - Lista de diccionarios con info de cada resultado
    """
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    # Preparar la consulta. Puedes ajustar el prompt según tu caso.
    query = f"{profession} in {country} contact email"
    
    payload = {
        "q": query,
        # Ajusta si quieres más resultados por página o páginas adicionales
        # "num": num_results
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            # Serper retorna resultados en 'organic' generalmente
            results = data.get("organic", [])
            return results
        else:
            st.error(f"Error {response.status_code}: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error al hacer la solicitud: {e}")
        return []

# -------------------------------------------------------------
# Función para extraer texto de una URL y buscar emails con regex
# -------------------------------------------------------------
def scrape_emails_from_url(link):
    """
    Dado un link, realiza un GET y extrae todos los correos electrónicos
    del HTML. Retorna una lista de correos únicos.
    """
    email_pattern = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    emails_found = set()
    try:
        resp = requests.get(link, timeout=10, allow_redirects=True)
        if resp.status_code == 200:
            # Extraer todos los emails del texto
            matches = email_pattern.findall(resp.text)
            for m in matches:
                emails_found.add(m)
    except Exception:
        pass
    return list(emails_found)

# -------------------------------------------------------------
# STREAMLIT APP
# -------------------------------------------------------------
def main():
    st.title("Búsqueda de profesionales y extracción de emails")

    # Campos de texto para ingresar profesión y país
    profession = st.text_input("Profesión (ej. 'Arquitecto', 'Abogado')", "")
    country = st.text_input("País (ej. 'España', 'México')", "")

    # Campo para limitar la cantidad de contactos
    max_contacts = st.number_input("Máximo de contactos a obtener", min_value=10, max_value=1000, value=500, step=10)

    st.write("**Atención**: Presiona el botón y espera unos segundos mientras se recopilan los datos.")

    if st.button("Buscar y extraer emails"):
        if not profession or not country:
            st.warning("Ingresa ambos campos: profesión y país.")
            return
        
        # 1. Cargar la API Key desde secrets
        api_key = st.secrets["SERPER"]["API_KEY"]

        # 2. Hacer la búsqueda
        st.write(f"Buscando '{profession}' en {country} ...")
        results = search_web(profession, country, api_key)
        
        if not results:
            st.warning("No se encontraron resultados o ocurrió un error en la búsqueda.")
            return
        
        # 3. Recorrer resultados y extraer correos
        #    Nota: Cada item en results tiene keys como "title", "link", "snippet" (dependiendo del JSON devuelto)
        all_emails = set()
        
        for item in results:
            link = item.get("link")
            if link:
                found = scrape_emails_from_url(link)
                for email in found:
                    if len(all_emails) < max_contacts:
                        all_emails.add(email)
                    else:
                        break
            # Detenernos si ya llegamos a los 500 (o max_contacts)
            if len(all_emails) >= max_contacts:
                break
        
        # 4. Crear DataFrame con los resultados
        df = pd.DataFrame({"Email": list(all_emails)})

        st.write(f"Se encontraron {len(df)} correos electrónicos.")
        st.dataframe(df)

        # 5. Generar botón de descarga de Excel
        if not df.empty:
            @st.cache_data
            def to_excel(dataframe):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    dataframe.to_excel(writer, index=False, sheet_name="Contactos")
                return output.getvalue()

            excel_file = to_excel(df)
            st.download_button(
                label="Descargar Excel",
                data=excel_file,
                file_name=f"contactos_{profession}_{country}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
