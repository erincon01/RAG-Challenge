import os
import json
import pandas as pd

import psycopg2
from psycopg2 import sql


def load_lineups_data(server, database, username, password, dir_source, num_files = -1, interactive = False):

    # Conectar a la base de datos
    conn = psycopg2.connect(
        host=server,
        database=database,
        user=username,
        password=password
    )
    
    cursor = conn.cursor()
    # archivos de events

    eventsPath = os.path.join(dir_source, 'lineups')

    for root, dirs, files in os.walk(eventsPath):

        # Pintar en pantalla el número de archivos a procesar
        # pedir al usuario confirmación para seguri adelante
        print(f"Se van a procesar {len(files)} archivos de [alineaciones]...")
        print("---------------------------------------------")

        # si interactive es True, preguntar al usuario si quiere seguir adelante
        if interactive:
            # si responde Y o y, seguir adelante, sino salir
            if input("¿Estás seguro de querer continuar? (Y/N): ").upper() != "Y":
                print("Proceso cancelado por el usuario.")
                return

        i=0

        for file in files:
            i+=1

            #si i+1>num_files, salir
            if num_files > 0 and i+1 > num_files:
                break

            if file.endswith(".json"):

                # el nombre del archivo es el match_id 134141.json (acorde a la documentación de statsbomb)

                filename = file
                filename = filename.replace('.json', '')
                filename = filename.split('\\')[-1]

                with open(os.path.join(eventsPath, file), 'r', encoding='utf-8', errors='replace') as f:
                    data = json.load(f)

                sql = """
                    INSERT INTO lineups (
                        match_id, 
                        home_team_id, home_team_name, 
                        away_team_id, away_team_name,
                        json_
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """

                # Parámetros de la consulta
                params = (
                    filename,
                    data[0]['team_id'], data[0]['team_name'].replace("'", "''"),
                    data[1]['team_id'], data[1]['team_name'].replace("'", "''"),
                    json.dumps(data).replace("'", "''")  # Escapar comillas simples en JSON
                )

                # Ejecutar la consulta SQL con parámetros
                cursor.execute(sql, params)

                # Hacer commit de los cambios
                conn.commit()

                if i % 10 == 0:
                    print(f"Alineaciones ({i}/{len(files)}). Insertados datos del match_id [{filename}]: {data[0]['team_name']}, {data[1]['team_name']}")

    # Cerrar la conexión
    cursor.close()
    conn.close()


def load_events_data(server, database, username, password, dir_source, num_files = -1, interactive = False):
    # Conectar a la base de datos
    conn = psycopg2.connect(
        host=server,
        database=database,
        user=username,
        password=password
    )
    
    cursor = conn.cursor()

    # Ruta de los archivos de eventos
    eventsPath = os.path.join(dir_source, 'events')

    for root, dirs, files in os.walk(eventsPath):

        # Pintar en pantalla el número de archivos a procesar
        # pedir al usuario confirmación para seguri adelante
        print(f"Se van a procesar {len(files)} archivos de [Eventos]...")
        print("---------------------------------------------")

        # si interactive es True, preguntar al usuario si quiere seguir adelante
        if interactive:
            # si responde Y o y, seguir adelante, sino salir
            if input("¿Estás seguro de querer continuar? (Y/N): ").upper() != "Y":
                print("Proceso cancelado por el usuario.")
                return

        i = 0

        for file in files:

            i += 1

            #si i+1>num_files, salir
            if num_files > 0 and i+1 > num_files:
                break

            if file.endswith(".json"):

                # El nombre del archivo es el match_id, como 134141.json (acorde a la documentación)
                match_id = file.replace('.json', '')

                with open(os.path.join(eventsPath, file), 'r', encoding='utf-8', errors='replace') as f:
                    data = json.load(f)

                j = 0

                sql = """
                    INSERT INTO events (
                        match_id, json_
                    )
                    VALUES (%s, %s)
                """

                # Extraer los datos necesarios del evento
                params = (
                    match_id,
                    json.dumps(data).replace("'", "''")  # Escapar comillas simples en JSON
                )                

                # Ejecutar la consulta SQL con parámetros
                cursor.execute(sql, params)

                # Hacer commit de los cambios
                conn.commit()
                
                # Iterar sobre cada evento en la lista de eventos del JSON
                for event in data: 

                    j += 1 
                    z = len(data)

                    #si i+1>num_files, salir
                    if num_files > 0 and j+1 > num_files:
                        break

                    # Preparar la consulta SQL
                    sql = """
                        INSERT INTO events_details (
                            match_id, timestamp, period, type, 
                            possession_team, play_pattern, team, json_
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    # Extraer los datos necesarios del evento
                    params = (
                        match_id,
                        f"{event['timestamp']}",  # Asumimos que timestamp ya está en formato correcto
                        event['period'],
                        event['type']['name'].replace("'", "''"),  # Escapar comillas simples
                        event['possession_team']['name'].replace("'", "''"),
                        event['play_pattern']['name'].replace("'", "''"),
                        event['team']['name'].replace("'", "''"),
                        json.dumps(event).replace("'", "''")  # Escapar comillas simples en JSON
                    )

                    # Ejecutar la consulta SQL con parámetros
                    cursor.execute(sql, params)

                    # Hacer commit de los cambios
                    conn.commit()

                    if j % 10 == 0:
                        print(f"Eventos ({i}/{len(files)})({j}/{z}). Insertados datos del mach_id [{file}]: Evento: {event['team']['name']}")

    # Cerrar la conexión
    cursor.close()
    conn.close()


import os
import json
import psycopg2

def load_matches_data(server, database, username, password, dir_source, num_files=-1, interactive=False):
    # Connect to the database
    conn = psycopg2.connect(
        host=server,
        database=database,
        user=username,
        password=password
    )
    
    cursor = conn.cursor()

    # Path to the match files
    matchesPath = os.path.join(dir_source, 'matches')
    total_files = 0

    # Contar el número total de archivos JSON
    for dir in os.listdir(matchesPath):
        dir_path = os.path.join(matchesPath, dir)
        
        # Verificar si es un directorio
        if os.path.isdir(dir_path):
            # Iterar sobre cada archivo en el directorio
            for file in os.listdir(dir_path):
                if file.endswith(".json"):
                    total_files += 1  # Incrementar el contador por cada archivo JSON

    print(f"Se van a procesar {total_files} archivos de [Matches]...")
    print("---------------------------------------------")

    if interactive:
        if input("¿Estás seguro de querer continuar? (Y/N): ").upper() != "Y":
            print("Proceso cancelado por el usuario.")
            return

    i=0
    j=0

    for dir in os.listdir(matchesPath):
        dir_path = os.path.join(matchesPath, dir)
        
        # Verificar si es un directorio
        if os.path.isdir(dir_path):
            # Iterar sobre cada archivo en el directorio
            for file in os.listdir(dir_path):

                if file.endswith(".json"):

                    i+=1
                    if num_files > 0 and i > num_files:
                        break

                    file_path = os.path.join(dir_path, file)

                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        season_data = json.load(f)

                    j=0
                    for data in season_data:
                        j += 1
                        # Insert match data
                        sql = """
                            INSERT INTO matches (
                                match_id, match_date, competition_id, competition_name,
                                season_id, season_name, 
                                home_team_id, home_team_name,
                                away_team_id, away_team_name, 
                                home_score, away_score,
                                stadium_id, stadium_name,result,
                                json_
                            )
                            VALUES (%s, %s, %s, %s, 
                            %s, %s, %s, %s, %s, %s, %s, %s, 
                            %s, %s, %s,
                            %s)
                        """
                        params = (
                            data['match_id'],
                            data['match_date'],
                            data['competition']['competition_id'],
                            data['competition']['competition_name'].replace("'", "''"),
                            data['season']['season_id'],
                            data['season']['season_name'].replace("'", "''"),
                            data['home_team']['home_team_id'],
                            data['home_team']['home_team_name'].replace("'", "''"),
                            data['away_team']['away_team_id'],
                            data['away_team']['away_team_name'].replace("'", "''"),
                            data['home_score'],
                            data['away_score'],
                            data.get('stadium', {}).get('id', None), # a veces el estadio viene vacio
                            data.get('stadium', {}).get('name', '').replace("'", "''"),  # a veces el estadio viene vacio
                            f"{data['home_score']} - {data['away_score']}",
                            json.dumps(data).replace("'", "''")
                        )
                        cursor.execute(sql, params)
                        conn.commit()

                        home = data['home_team']['home_team_name'].replace("'", "''")
                        away = data['away_team']['away_team_name'].replace("'", "''")

                        if j % 10 == 0:
                            print(f"Partidos ({i}-{j}/{total_files}: {file}): Insertados datos - match_id:{data['match_id']}, {data['match_date']}, {home}-{away}")

                        if num_files > 0 and j >= num_files:
                            break

    cursor.close()
    conn.close()
    print(f"Proceso completado. Se procesaron {i} archivos.")


def update_embeddings(server, database, username, password, model, tablename, batch_size, num_rows=-1):

    # si model es azure_open_ai, usar la función create_embeddings de azure_openai
    # si model es azure_local_ai, usar la función create_embeddings de azure_local_ai

    function_name = ""
    model_name = ""
    if model == "azure_open_ai":
        function_name = "azure_openai.create_embeddings"
        model_name = "text-embedding-ada-002"
        
    elif model == "azure_local_ai":
        function_name = "azure_local_ai.create_embeddings"  # Cambiar por el nombre correcto de la función
        model_name = "multilingual-e5-small:v1"  # Cambiar por el nombre correcto del modelo

    else:
        print(f"Modelo no soportado: {model}")
        return

    try:        
        # Connect to the database
        conn = psycopg2.connect(
            host=server,
            database=database,
            user=username,
            password=password
        )
        
        cursor = conn.cursor()

        # pintar servidor y base de datos
        
        # contar las filas que no tienen embeddings y pintarlo en pantalla
        count_query = sql.SQL(f"""
            SELECT COUNT(*) FROM {tablename}
            WHERE embeddings IS NULL AND json_ IS NOT NULL
        """)
        cursor.execute(count_query)
        count = cursor.fetchone()[0]
        print(f"Total de filas en tabla [{tablename}] sin procesar: {count}. Tamaño del lote {batch_size}.", end="")

        # Consulta para actualizar las filas
        update_query = sql.SQL(f"""
            UPDATE {tablename}
            SET embeddings = {function_name}('{model_name}', json_)
            WHERE id IN (
                SELECT id FROM {tablename} 
                WHERE embeddings IS NULL AND 
                json_ IS NOT NULL
                LIMIT {batch_size}
            )
        """)

        processed_rows = 0

        while True:
            cursor.execute(update_query)
            conn.commit()
            rows_affected = cursor.rowcount
            processed_rows += rows_affected

            # Romper el bucle si no se afectaron filas (cuando no hay más filas que coincidan con la condición)
            if rows_affected == 0:
                break

            # pintar punto sin saltar de linea
            print(".", end="")

            # Imprimir cada 10 iteraciones si num_rows es diferente de -1
            if (processed_rows % 100 == 0):
                print()
                print(f"Procesado {processed_rows} filas.", end="")
            
            # Romper el bucle si alcanzamos el número de filas a actualizar especificado
            if num_rows != -1 and processed_rows >= num_rows:
                break

        print(f"Total de filas procesadas: {processed_rows}.")

    except Exception as e:
        print(f"Error al conectar o ejecutar la consulta en la base de datos: {e}")

    finally:
        # Cerrar el cursor y la conexión
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def put_data_into_postgres(server, database, username, password, dir_source):

    # load_lineups_data(server, database, username, password, dir_source, -1, interactive=False)
    # load_events_data(server, database, username, password, dir_source, -1, interactive=False)
    load_matches_data(server, database, username, password, dir_source, -1, interactive=False)
