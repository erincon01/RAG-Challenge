import os
import requests
import pandas as pd

def fetch_json_data(url):

    # Obtiene datos JSON de una URL
    response = requests.get(url)
    response.raise_for_status()  # Lanza excepción para códigos de estado HTTP 4xx/5xx
    return response.json()


def obtener_lista_jsons(repo_owner, repo_name, dataset):
    
    # Construir la URL de la API de GitHub
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/data/{dataset}"
    
    try:
        # Realizar la solicitud a la API
        response = requests.get(api_url)
        json_files = []

        if response.status_code == 200:
            files = response.json()
            json_files = [[dataset, "", file['download_url']] for file in files if file['name'].endswith('.json')]
            # si json_urls no está vacío, retornar la lista de URLs
            if not json_files:
                # procesar subdirectorios (ejemplo de directorio matches)
                # sacar de files la propiedad name que contiene el nombre del directorio
                subdirs = [file['name'] for file in files if file['type'] == 'dir']
                # si hay subdirectorios, llamar recursivamente a la función
                if subdirs:
                    for subdir in subdirs:
                        # añadir a api_url el nombre del subdirectorio
                        response = requests.get(f"{api_url}/{subdir}")
                        if response.status_code == 200:
                            files = response.json()
                            json_files += [[dataset, subdir, file['download_url']] for file in files if file['name'].endswith('.json')]
                        else:
                            print(f"Error al obtener los archivos: {response.status_code, response.text}")
        else:
            print(f"Error al obtener los archivos: {response.status_code, response.text}")

    except requests.exceptions.HTTPError as http_err:
        print(f"Error HTTP: {http_err}")
    except requests.exceptions.ConnectionError:
        print("Error de conexión. Verifica tu conexión a internet.")
    except requests.exceptions.Timeout:
        print("La solicitud ha superado el tiempo de espera.")
    except requests.exceptions.RequestException as err:
        print(f"Error al realizar la solicitud: {err}")
    except ValueError:
        print("Error al procesar la respuesta JSON.")
    except Exception as e:
        print(f"Se produjo un error inesperado: {e}")

    df = pd.DataFrame(json_files, columns=["dataset", "subdir", "url"])
    return df

def descargar_archivo(url, path, dir, subdir):

    # Verifica si el path existe
    if not os.path.exists(path):
        print(f"El path '{path}' no existe. Abortando.")
        return

    # Crea el directorio y subdirectorio si no existen
    directorio_destino = os.path.join(path, dir, subdir)
    os.makedirs(directorio_destino, exist_ok=True)

    try:
        # Realiza la solicitud GET al archivo
        response = requests.get(url)
        response.raise_for_status()  # Lanza una excepción para códigos de estado de error HTTP

        # Extrae el nombre del archivo de la URL
        nombre_archivo = os.path.basename(url)

        # Construye la ruta completa para guardar el archivo
        ruta_archivo = os.path.join(directorio_destino, nombre_archivo)

        # Guarda el archivo en el directorio de destino
        with open(ruta_archivo, 'wb') as file:
            file.write(response.content)

        print(f"Archivo descargado exitosamente en {ruta_archivo}")

    except requests.exceptions.HTTPError as http_err:
        print(f"Error HTTP: {http_err}")
    except requests.exceptions.ConnectionError:
        print("Error de conexión. Verifica tu conexión a internet.")
    except requests.exceptions.Timeout:
        print("La solicitud ha superado el tiempo de espera.")
    except requests.exceptions.RequestException as err:
        print(f"Error al realizar la solicitud: {err}")
    except Exception as e:
        print(f"Se produjo un error inesperado: {e}")

def get_github_data(repo_owner, repo_name, datasets, dir_destino):

    # para cada dataset
    for dataset in datasets:
        direcciones_json = obtener_lista_jsons(repo_owner, repo_name, dataset)

        # asignar en variable c el resultado de group by de dataset, contando el numero de registros por dataset
        c = direcciones_json.groupby(['dataset']).size().reset_index(name='counts')
        print(c)

        for _, row in direcciones_json.iterrows():
            dataset = row['dataset']
            subdir = row['subdir']
            file_url = row['url']
            print(f"dataset: {dataset}, subdir: {subdir}, url: {file_url}")

            descargar_archivo(file_url, dir_destino, dataset, subdir)

