import os
import json
import requests
import psycopg2
from psycopg2 import sql
import pandas as pd
from module_github import get_github_data
from module_postgresql import put_data_into_postgres, update_embeddings

if __name__ == "__main__":

    # get data from github and store in local

    repo_owner = os.getenv('REPO_OWNER')
    repo_name = os.getenv('REPO_NAME')
    datasets = os.getenv('DATASETS')
    dir_destino = os.getenv('DIR_DESTINO')
    dir_source = os.getenv('DIR_FUENTE')
    
    # remove wait spaces
    datasets = datasets.split(',')
    datasets = [dataset.strip() for dataset in datasets]

    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')

    # bajar datos desde repositorio de github a directorio destino (dir_destino)
    # get_github_data (repo_owner, repo_name, datasets, dir_destino)

    dir_source = dir_destino

    # cargar datos en postgres desde directorio fuente (dir_source)
    # put_data_into_postgres(server, database, username, password, dir_destino)

    # for azure_open_ai, o azure_local_ai
    model = "azure_local_ai" # azure_open_ai, 
    # azure_local_ai (ver documentación azure_open_ai solo soportado en regiones concretas y Memory Optimized, E4ds_v5, 4 vCores, 32 GiB RAM, 128 GiB storage)

    update_embeddings(server, database, username, password, model, "events", 10, -1) # tabla events tiene json_ enorme, dificil de procesar en azure_open_ai
    update_embeddings(server, database, username, password, model, "lineups", 10,  -1)
    update_embeddings(server, database, username, password, model, "events_details", 10, -1)
    update_embeddings(server, database, username, password, model, "matches", 10, -1)

