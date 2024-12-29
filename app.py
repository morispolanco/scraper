import streamlit as st
import requests
import pandas as pd
from io import BytesIO

# Título de la aplicación
st.title("Buscador de Correos Electrónicos de Profesionales")

# Descripción de la aplicación
st.markdown("""
Esta aplicación permite buscar correos electrónicos de profesionales específicos en un país determinado utilizando la API de [exa.ai](https://exa.ai/).
  
**Instrucciones:**
1. Ingresa el tipo de profesional (por ejemplo, "abogados").
2. Ingresa el país (por ejemplo, "Guatemala").
3. Haz clic en "Iniciar Búsqueda".
4. Visualiza los resultados y descárgalos en formato Excel.
""")

# Formulario de entrada
with st.form(key='search_form'):
    # Entrada para el tipo de profesional
    profesional = st.text_input("Tipo de Profesional", value="abogados")
    
    # Entrada para el país
    pais = st.text_input("País", value="Guatemala")
    
    # Botón para iniciar la búsqueda
    buscar = st.form_submit_button(label='Iniciar Búsqueda')

# Función para realizar la búsqueda utilizando la API de exa.ai
def buscar_correos(profesional, pais, api_key):
    url = "https://api.exa.ai/search"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": api_key
    }
    
    # Construcción de la consulta
    query = f"Emails de {profesional} de {pais} en LinkedIn"
    
    payload = {
        "query": query,
        "type": "auto",
        "numResults": 50
    }
    
    try:
        # Realizar la solicitud POST a la API
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
        
        # Procesar la respuesta JSON
        data = response.json()
        
        # Supongamos que los resultados están en 'results'
        resultados = data.get('results', [])
        
        # Convertir los resultados a un DataFrame de pandas
        df = pd.DataFrame(resultados)
        
        return df
    
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP: {http_err}")
    except Exception as err:
        st.error(f"Ocurrió un error: {err}")
    
    return pd.DataFrame()  # Retorna un DataFrame vacío en caso de error

# Si el usuario ha enviado el formulario
if buscar:
    # Mostrar un mensaje de carga
    with st.spinner('Buscando correos electrónicos...'):
        # Obtener la clave API desde los secretos de Streamlit
        api_key = st.secrets["API_KEY"]
        
        # Realizar la búsqueda
        resultados_df = buscar_correos(profesional, pais, api_key)
    
    # Verificar si se obtuvieron resultados
    if not resultados_df.empty:
        st.success("Búsqueda completada exitosamente.")
        
        # Mostrar los resultados en la aplicación
        st.dataframe(resultados_df)
        
        # Función para convertir el DataFrame a un archivo Excel descargable
        def convert_df_to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Resultados')
                writer.save()
            processed_data = output.getvalue()
            return processed_data
        
        # Convertir el DataFrame a Excel
        excel_data = convert_df_to_excel(resultados_df)
        
        # Botón para descargar el archivo Excel
        st.download_button(
            label="Descargar Resultados en Excel",
            data=excel_data,
            file_name='resultados.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.warning("No se encontraron resultados para la búsqueda especificada.")
