import streamlit as st
import requests
import pandas as pd
from io import BytesIO
import re

# Función para validar correos electrónicos
def es_email_valido(email):
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(patron, email) is not None

# Título de la aplicación
st.title("Buscador de Correos Electrónicos de Profesionales")

# Descripción de la aplicación
st.markdown("""
Esta aplicación permite buscar correos electrónicos de profesionales específicos en un país determinado utilizando la API de [exa.ai](https://exa.ai/).

**Instrucciones:**
1. Ingresa el tipo de profesional (por ejemplo, "abogados").
2. Ingresa el país (por ejemplo, "Guatemala").
3. Especifica el número de correos electrónicos que deseas obtener (de 50 a 5000).
4. Haz clic en "Iniciar Búsqueda".
5. Visualiza los resultados y descárgalos en formato Excel.
""")

# Formulario de entrada
with st.form(key='search_form'):
    # Entrada para el tipo de profesional
    profesional = st.text_input("Tipo de Profesional", value="abogados")
    
    # Entrada para el país
    pais = st.text_input("País", value="Guatemala")
    
    # Entrada para el número de correos electrónicos
    num_emails = st.number_input(
        "Número de Correos Electrónicos",
        min_value=50,
        max_value=5000,
        value=50,
        step=50,
        help="Ingresa un número entre 50 y 5000."
    )
    
    # Botón para iniciar la búsqueda
    buscar = st.form_submit_button(label='Iniciar Búsqueda')

# Función para realizar la búsqueda utilizando la API de exa.ai
def buscar_correos(profesional, pais, num_emails, api_key):
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
        "numResults": num_emails
    }
    
    try:
        # Realizar la solicitud POST a la API
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
        
        # Procesar la respuesta JSON
        data = response.json()
        
        # Mostrar la respuesta completa para depuración (elimina esto después)
        # st.write("Respuesta completa de la API:", data)
        
        # Supongamos que los resultados están en 'results'
        resultados = data.get('results', [])
        
        # Extraer los correos electrónicos y otros campos relevantes
        emails = []
        otros_datos = []
        
        for item in resultados:
            # Intentar obtener el correo electrónico dentro de 'contact'
            contact = item.get('contact', {})
            email = contact.get('email', None)
            
            # Si no se encuentra, intentar en otra clave (ejemplo: 'emails')
            if not email:
                # Suponiendo que 'emails' es una lista
                emails_list = item.get('emails', [])
                email = emails_list[0] if emails_list else None
            
            # Validar el correo electrónico
            if email and es_email_valido(email):
                emails.append(email)
            else:
                emails.append("No disponible")
            
            # Extraer otros datos si están disponibles
            otros_datos.append({
                "Nombre": item.get('name', 'No disponible'),
                "Posición": item.get('position', 'No disponible'),
                "Empresa": item.get('company', 'No disponible'),
                # Añade más campos según la respuesta de la API
            })
        
        # Crear un DataFrame con los correos electrónicos y otros datos
        df_emails = pd.DataFrame({'Emails': emails})
        df_otros = pd.DataFrame(otros_datos)
        
        # Combinar los DataFrames en uno solo
        df_final = pd.concat([df_otros, df_emails], axis=1)
        
        return df_final
    
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP: {http_err}")
    except Exception as err:
        st.error(f"Ocurrió un error: {err}")
    
    return pd.DataFrame()  # Retorna un DataFrame vacío en caso de error

# Función para convertir el DataFrame a un archivo Excel descargable
def convert_df_to_excel(df):
    output = BytesIO()
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Resultados')
            writer.save()
        processed_data = output.getvalue()
        return processed_data
    except ImportError:
        st.error("La biblioteca 'xlsxwriter' no está instalada. Por favor, instala 'xlsxwriter' para habilitar la exportación a Excel.")
    except Exception as e:
        st.error(f"Ocurrió un error al convertir a Excel: {e}")
    return None

# Si el usuario ha enviado el formulario
if buscar:
    # Validar el número de correos electrónicos
    if not 50 <= num_emails <= 5000:
        st.error("El número de correos electrónicos debe estar entre 50 y 5000.")
    else:
        # Mostrar un mensaje de carga
        with st.spinner('Buscando correos electrónicos...'):
            # Obtener la clave API desde los secretos de Streamlit
            api_key = st.secrets["API_KEY"]
            
            # Realizar la búsqueda
            resultados_df = buscar_correos(profesional, pais, num_emails, api_key)
        
        # Verificar si se obtuvieron resultados
        if not resultados_df.empty:
            st.success("Búsqueda completada exitosamente.")
            
            # Mostrar los resultados en la aplicación
            st.dataframe(resultados_df)
            
            # Convertir el DataFrame a Excel
            excel_data = convert_df_to_excel(resultados_df)
            
            if excel_data:
                # Botón para descargar el archivo Excel
                st.download_button(
                    label="Descargar Resultados en Excel",
                    data=excel_data,
                    file_name='resultados.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
        else:
            st.warning("No se encontraron resultados para la búsqueda especificada.")
