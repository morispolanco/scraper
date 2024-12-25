import streamlit as st
import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
from io import BytesIO
from googlesearch import search

def extraer_emails_de_url(url):
    """
    Dada una URL, intenta extraer emails del contenido HTML.
    Retorna una lista con todos los emails encontrados (sin duplicados).
    """
    emails_encontrados = set()
    
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/58.0.3029.110 Safari/537.36"
            )
        }
        respuesta = requests.get(url, headers=headers, timeout=10)
        
        # Si la respuesta es exitosa (código 200), parseamos
        if respuesta.status_code == 200:
            # Extraemos texto
            texto = respuesta.text
            # Regex para buscar emails
            posibles_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+', texto)
            for email in posibles_emails:
                emails_encontrados.add(email)
    except Exception as e:
        # Si algo falla, mostramos el error en consola.
        print(f"Error al procesar la URL {url}: {e}")

    return list(emails_encontrados)

def main():
    st.title("Búsqueda de perfiles de LinkedIn y extracción de emails")
    
    # Inputs del usuario
    profesion = st.text_input("Profesión / Cargo", value="Data Scientist")
    pais = st.text_input("País", value="Colombia")
    
    # Botón para iniciar la búsqueda
    if st.button("Buscar y extraer emails"):
        if profesion and pais:
            st.write("Buscando páginas de LinkedIn relacionadas...")
            
            # Construimos la query para Google
            query = f"site:linkedin.com/in/ {profesion} {pais}"
            
            # Realizamos la búsqueda en Google (máximo 10 resultados)
            resultados = []
            for url in search(query, tld="com", lang="es", num=10, stop=10, pause=2):
                resultados.append(url)

            st.write(f"Encontradas {len(resultados)} URL(s):")
            for r in resultados:
                st.write(r)

            # Extraer emails de cada URL
            todos_emails = []
            for url in resultados:
                emails = extraer_emails_de_url(url)
                for e in emails:
                    todos_emails.append({"url": url, "email": e})

            if todos_emails:
                st.write("Emails extraídos:")
                df_emails = pd.DataFrame(todos_emails)
                st.dataframe(df_emails)

                # Generar archivo Excel en memoria
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_emails.to_excel(writer, index=False, sheet_name='Emails')
                
                # Botón de descarga
                st.download_button(
                    label="Descargar Excel",
                    data=output.getvalue(),
                    file_name="emails_linkedin.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.write("No se encontraron emails en las páginas visitadas.")
        else:
            st.warning("Por favor, introduce tanto la profesión como el país.")

if __name__ == "__main__":
    main()
