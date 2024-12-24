import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import time

# Configuración de la API de Serper
SERPER_API_KEY = st.secrets["SERPER_API_KEY"]
SERPER_URL = 'https://google.serper.dev/search'
HEADERS = {
    'X-API-KEY': SERPER_API_KEY,
    'Content-Type': 'application/json'
}

# Función para realizar una búsqueda en Serper
def search_serper(query):
    payload = {"q": query}
    response = requests.post(SERPER_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error al realizar la búsqueda en Serper: {response.status_code} - {response.text}")
        return None

# Función para extraer información de una URL
def scrape_website(url):
  try:
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        return text_content
    else:
        st.error(f"Error al obtener el contenido de la URL {url}: {response.status_code}")
        return ""
  except requests.exceptions.RequestException as e:
    st.error(f"Error de conexión al obtener {url}: {e}")
    return ""

# Función para extraer correos y teléfonos de un texto
def extract_contacts(text):
  emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
  phones = re.findall(r"(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})", text)
  return emails, phones

# Función principal de la aplicación
def main():
  st.title("Buscador de Contactos Profesionales")

  profesion = st.text_input("Profesión a buscar (ej: Abogado, Médico, Ingeniero):")
  pais = st.text_input("País a buscar (ej: España, México, Argentina):")

  if st.button("Buscar Contactos"):
    if not profesion or not pais:
        st.warning("Por favor, ingrese la profesión y el país.")
        return

    st.info(f"Buscando profesionales de {profesion} en {pais}... Esto puede tomar un tiempo.")

    all_contacts = []
    contactos_encontrados = 0
    page = 1

    while contactos_encontrados < 500:
      query = f"Directorio de {profesion} {pais} página {page}"
      st.write(f"Búsqueda: {query}")
      search_results = search_serper(query)

      if search_results and "organic" in search_results:
        for result in search_results["organic"]:
          if contactos_encontrados >= 500:
            break
          url = result.get("link")
          if url:
              st.write(f"Extrayendo información de: {url}")
              page_content = scrape_website(url)
              if page_content:
                  emails, phones = extract_contacts(page_content)
                  for email in emails:
                    if contactos_encontrados >= 500:
                      break
                    all_contacts.append({"Profesión": profesion, "País": pais, "Email": email, "Teléfono": "N/A", "Fuente": url})
                    contactos_encontrados += 1
                  for phone in phones:
                    if contactos_encontrados >= 500:
                      break
                    all_contacts.append({"Profesión": profesion, "País": pais, "Email": "N/A", "Teléfono": phone, "Fuente": url})
                    contactos_encontrados += 1
              else:
                st.warning(f"No se pudo obtener el contenido de la URL: {url}")
          else:
            st.warning(f"No se encontró la URL en el resultado: {result}")
        page +=1
      else:
        st.warning(f"No se encontraron resultados para {query} en la página {page}. Finalizando búsqueda...")
        break

      if contactos_encontrados >= 500:
          st.success(f"Se encontraron {contactos_encontrados} contactos. ¡Límite alcanzado!")
          break
      
      time.sleep(2)  # Pausa para no sobrecargar el servidor

    if all_contacts:
      df = pd.DataFrame(all_contacts)
      st.write("### Resultados:")
      st.dataframe(df)
      
      # Descargar como Excel
      excel_file = df.to_excel("contactos_profesionales.xlsx", index=False)

      with open("contactos_profesionales.xlsx", "rb") as file:
        st.download_button(
            label="Descargar Excel",
            data=file,
            file_name="contactos_profesionales.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
      st.info("No se encontraron contactos con los criterios de búsqueda.")
    
if __name__ == "__main__":
    main()
