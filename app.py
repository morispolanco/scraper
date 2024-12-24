import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import time

# Función para realizar búsquedas con Serper
def search_serper(query, api_key):
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    data = {"q": query}
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status() # Lanza una excepción si la petición falla
        return response.json()
    except requests.exceptions.RequestException as e:
         st.error(f"Error en la consulta a la API de Serper: {e}")
         return None

# Función para extraer correos electrónicos de texto HTML
def extract_emails(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    emails = re.findall(email_pattern, text)
    return emails

# Función para extraer información de un directorio
def extract_from_directory(url):
    try:
      response = requests.get(url)
      response.raise_for_status()
      emails = extract_emails(response.text)
      return emails
    except requests.exceptions.RequestException as e:
      st.error(f"Error al acceder a la URL {url}: {e}")
      return None

# Aplicación Streamlit
def main():
    st.title("Búsqueda de Contactos Profesionales")

    # Obtener la API key de Streamlit Secrets
    api_key = st.secrets["SERPER_API_KEY"]

    profession = st.text_input("Profesión a buscar:", "abogados")
    country = st.text_input("País a buscar:", "Colombia")
    max_contacts = st.number_input("Máximo de contactos:", min_value=1, max_value=500, value=100)
    search_button = st.button("Buscar")


    if search_button:
      st.spinner("Buscando directorios y asociaciones...")

      # Realizar la búsqueda en Serper
      query = f"directorio de {profession} en {country}"
      search_results = search_serper(query, api_key)

      if search_results and "organic" in search_results:
        directory_urls = [item["link"] for item in search_results["organic"]]
      else:
        st.warning("No se encontraron directorios relevantes.")
        directory_urls = []

      all_emails = []
      if directory_urls:
          progress_bar = st.progress(0)
          num_urls = len(directory_urls)
          for i, url in enumerate(directory_urls):
              st.write(f"Extrayendo emails de {url}")
              emails = extract_from_directory(url)
              if emails:
                  all_emails.extend(emails)
              progress_bar.progress((i+1)/num_urls)
              time.sleep(1) # Pausa para no sobrecargar la página web
              if len(all_emails) >= max_contacts:
                  break
          
          all_emails = list(set(all_emails)) # Eliminar duplicados
      else:
          st.warning("No se encontraron directorios.")
      
      if all_emails:
        df = pd.DataFrame(all_emails, columns=["Email"])
        st.success(f"Se encontraron {len(all_emails)} emails.")
        st.download_button(
          label="Descargar CSV",
          data=df.to_csv(index=False).encode('utf-8'),
          file_name=f'{profession.replace(" ", "_")}_contacts.csv',
          mime='text/csv'
          )
        st.dataframe(df)
      else:
          st.warning("No se encontraron emails en los directorios.")


if __name__ == "__main__":
    main()
