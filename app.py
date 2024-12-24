import streamlit as st
import requests
import json

def main():
    st.title("Búsqueda con Serper")

    st.write("Este ejemplo envía la consulta 'apple inc' a la API de Serper y muestra la respuesta en pantalla.")

    # Carga la API Key almacenada en secrets.toml
    api_key = st.secrets["SERPER"]["API_KEY"]

    # Definimos la URL y los encabezados
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    # Define el payload, por ejemplo la búsqueda "apple inc"
    payload = {
        "q": "apple inc"
    }

    if st.button("Enviar consulta"):
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                st.write("### Respuesta de la API:")
                st.json(data)  # Muestra la respuesta completa en formato JSON
            else:
                st.error(f"Error {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"Ocurrió un error realizando la solicitud: {e}")

if __name__ == "__main__":
    main()
