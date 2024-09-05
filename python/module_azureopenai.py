import os
import subprocess
from datetime import datetime, timedelta

import psycopg2
from psycopg2 import sql

import pandas as pd

import openai

import openai

def get_script(endpoint, key, model, content, prompt):
    # Establecer la clave de la API de OpenAI
    openai.api_key = key

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": content},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150
    )

    # Obtener la respuesta generada por el modelo
    return response['choices'][0]['message']['content'].strip()



def get_events_fromDB (server, database, username, password, match_id, period, timestamp_from, timestamp_to):

      # Connect to the database
    conn = psycopg2.connect(
        host=server,
        database=database,
        user=username,
        password=password
    )
    
    cursor = conn.cursor()

    sql = f"""
            select json_
            from events_details
            where match_id = '{match_id}'
            and period = '{period}'
            and timestamp between '{timestamp_from}' and '{timestamp_to}'
            order by timestamp;
            """    
    cursor.execute(sql)

    # convertir el resultado a un dataframe
    df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

    return df

if __name__ == "__main__":

    # Ejemplo de uso
    ollama = os.getenv('PATH_OLLAMA')
    cabecera = os.getenv('MESSAGE_HEADER')

    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')

    openai_model = os.getenv('OPENAI_MODEL')
    openai_key = os.getenv('OPENAI_KEY')
    openai_endpoint = os.getenv('OPENAI_ENDPOINT')

    match_id = 3943043
    batch_size = 60 # seconds
    from_time = 0  # seconds
    to_time = 45 * 60  # 45 minutos convertidos a segundos


    from openai import AzureOpenAI

    api_version = "2023-07-01-preview"

    # gets API Key from environment variable OPENAI_API_KEY
    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=openai_endpoint,
    )
    
    # Non-streaming:
    print("----- standard request -----")
    completion = client.chat.completions.create(
        model="impl-gpt-35-turbo-16k",
        messages=[
            {
                "role": "user",
                "content": "Say this is a test",
            },
        ],
    )
    print(completion.choices[0].message.content)


    # bucle for from_time hasta to_time con incremento de batch_size
    for i in range(from_time, to_time, batch_size):

        # Convertir el tiempo en segundos a formato de horas, minutos y segundos
        timestamp_from = str(timedelta(seconds=i)) + '.000'
        timestamp_to = str(timedelta(seconds=i+batch_size)) + '.000'

        # obtener json_ de la base de datos
        df = get_events_fromDB(server, database, username, password, match_id, 1, timestamp_from, timestamp_to)
        df_text = df.to_string(index=False)

        # obtener transcript con openAI
        prompt = f"{cabecera}: {df_text}"

        script = get_script(openai_endpoint, openai_key, openai_model, cabecera, df_text)

        print (script)



