# statsbomb-loader
statsbomb loader

## Instala las dependencias:

Copiar código
```bash
pip install -r requirements.txt
```

## Configura las variables de entorno:

Rellena el archivo .env con tus datos.

```bash
    # URL base para acceder a los datos en GitHub
    BASE_URL=https://github.com/statsbomb/open-data/raw/master/data

    REPO_OWNER=statsbomb
    REPO_NAME=open-data
    DATASETS=events, lineups, matches, three-sixty
    DIR_DESTINO=./data
    DIR_FUENTE=./data

    # Configuración de la base de datos
    DB_SERVER=your_server_name.database.windows.net
    DB_NAME=your_database_name
    DB_USER=your_username
    DB_PASSWORD=your_password
```

Ejecuta el script:

```bash
python main.py
```


## utilización de vector databases en SQL PaaS:

- feature: https://github.com/Azure-Samples/azure-sql-db-vector-search
- requerimientos: https://github.com/Azure-Samples/azure-sql-db-vector-search?tab=readme-ov-file#prerequisites
- darse de alta: https://aka.ms/azuresql-vector-eap


## caso de uso

```bash
    +-----------------------------------------+
    |               Usuario                   |
    |-----------------------------------------|
    | Hace una pregunta al chatbot de OpenAI  |
    +-------------------+---------------------+
                        |
                        v
    +-------------------+---------------------+
    |           Chatbot de OpenAI             |
    |-----------------------------------------|
    | 1. Recibe la pregunta del usuario       |
    | 2. Envía la consulta al Plugin          |
    +-------------------+---------------------+
                        |
                        v
    +-------------------+---------------------+
    |           Plugin de Búsqueda            |
    |-----------------------------------------|
    | 1. Genera el embedding de la consulta   |
    |    utilizando OpenAI                    |
    | 2. Realiza una consulta semántica       |
    |    en la base de datos PostgreSQL       |
    +-------------------+---------------------+
                        |
                        v
    +-------------------+---------------------+
    |       PostgreSQL con pgvector           |
    |-----------------------------------------|
    | 1. Almacena datos de jugadores con      |
    |    embeddings                           |
    | 2. Realiza búsqueda basada en la        |
    |    similitud de embeddings              |
    | 3. Devuelve resultados relevantes       |
    +-------------------+---------------------+
                        |
                        v
    +-------------------+---------------------+
    |           Plugin de Búsqueda            |
    |-----------------------------------------|
    | 1. Recibe los resultados de PostgreSQL  |
    | 2. Genera un resumen o respuesta usando |
    |    OpenAI (si es necesario)             |
    +-------------------+---------------------+
                        |
                        v
    +-------------------+---------------------+
    |           Chatbot de OpenAI             |
    |-----------------------------------------|
    | 1. Recibe la respuesta del Plugin       |
    | 2. Presenta la respuesta al usuario     |
    +-----------------------------------------+

```
