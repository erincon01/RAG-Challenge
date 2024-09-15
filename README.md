# RAG Challenge

## Overview

Our team, [Sabados Tech](https://www.youtube.com/channel/UCw89YeTGdK74ZZ97_xcI2FA), is a passionate group of friends from Argentina and Spain who share two loves: football and technology. We meet weekly in virtual events to dive deep into Microsoft technologies, and our latest challenge brings us to the forefront of AI-driven data analysis. For this particular project, 2 SQL Server Former MVPs, and 1 .NET Former MVP haye joined forces: [Eugenio Serrano](https://www.linkedin.com/in/eugenio-serrano/), [José Mariano Álvarez](https://www.linkedin.com/in/josemarianoalvarez/) and [Eladio Rincón](https://www.linkedin.com/in/erincon/). [Eric](https://github.com/eric-net), [Walter](https://github.com/Exodo77), and [Nestor](https://github.com/nnarvaez) have helped too.

For the Microsoft RAG Hack Challenge, we aim to showcase the power of Retrieval-Augmented Generation (RAG) on Azure, combined with PostgreSQL and OpenAI extensions. Our project leverages advanced AI to analyze football match data, providing detailed insights into the beautiful game. Whether it’s breaking down player performance or reviewing match events, we’re using the latest cloud tools to transform raw data into actionable knowledge.

Together, we believe that football isn’t just a game – it’s data waiting to be unlocked, and we’re here to show the world how Microsoft Azure can be the key.

With the support of Microsoft - special thanks to [Bruno Capuano](https://x.com/elbruno) and  [Davide Mauri](https://x.com/mauridb), who are supportive to our community - we have processed match data from various football games, thanks to Azure resources provided by [Verne Tech](https://www.vernegroup.com/). In the remote event that we'd win the challenge, we will donate the price to [PROA school](https://www.cba.gov.ar/escuelas-proa/) in [Mina Clavero](https://www.minaclavero.gov.ar/), a fabulous city in the province of Cordoba, in Argentina.

We’d love to secure Azure credits to process the full set of matches from [StatsBomb](https://github.com/statsbomb/open-data) and develop a Version 2 of this project. Our goal is to make this initiative bigger, more consistent, and impactful processing ALL the open data exposed by Statsbomb.

Football is more than a game to us—it’s data, passion, and endless possibilities. WE LOVE FOOTBALL and with Azure and OpenAI, we’re ready to show the world just how powerful these technologies can be in transforming the way we analyze the sport we love!

## What we have built

- Data Loading: Download and import match data into PostgreSQL.
- Data Processing: Extract, summarize, and analyze match details.
- Integration: Interface with Azure for data transfer and use OpenAI for match summaries.
- Prompt based Q&A using phyton and RAG pattern.

## How to participate in the challenge

- WIP for Microsoft RAG challenge:
<https://github.com/microsoft/RAG_Hack?tab=readme-ov-file#raghack-lets-build-rag-applications-together>

- Official event: <https://reactor.microsoft.com/es-es/reactor/events/23332/>

## Environment setup

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Fill in the .env file with your data. see .env.example file.

```bash
######### statsbomb
BASE_URL=https://github.com/statsbomb/open-data/raw/master/data
REPO_OWNER=statsbomb
REPO_NAME=open-data
LOCAL_FOLDER=./data

######### postgres
DB_SERVER=server_name
DB_NAME=db_name
DB_USER=user_name
DB_PASSWORD=password

######### postgres Azure
DB_SERVER_AZURE=server_name.postgres.database.azure.com
DB_NAME_AZURE=db_name
DB_USER_AZURE=user_name
DB_PASSWORD_AZURE=password

######### Azure openai
OPENAI_MODEL=gpt-4o-mini
OPENAI_KEY=your_key
OPENAI_ENDPOINT=https://your_endpoint.openai.azure.com/
```

## Data preparation

Data preparacion consists in downloading the data to local folder.
Then store the data into local postgres, and then load the data into Azure postgres.
If needed help on seting up progres in local and Azure read read the relevent products documentation. These are some usefull links:

- <https://learn.microsoft.com/en-us/azure/postgresql/single-server/quickstart-create-server-database-portal>
- <https://www.docker.com/blog/how-to-use-the-postgres-docker-official-image/>

### Download data from statsbomb to local

This process download the data from Statsbomb to local.
The process is this:

- Download to local the data from all the `matches`.
- Stores into postgres the matches data.
- Based on the data stored into the dabase, then the `lineups`, and `events` data is downloaded.

**Note**: before step #2, you need to setup the postgres database locally, and create the relevant tables. Table script is located in the `postgres` folder, in the file `tables_setup_onprem.sql` [file path](./postgres/tables_setup_onprem.sql)

This process involves downloading data from a GitHub repository, storing it in a local folder, and optionally loading it into a PostgreSQL database for further analysis. The script `01-download_to_local.py` coordinates this process by utilizing methods from `module_github.py` and `module_postgres.py`.

#### Steps Involved

1. **Download Matches Data from GitHub Repository to Local Folder**  
   The method `download_data_from_github_repo` from `module_github.py` is used to download the data.

2. **Store Matches Data into PostgreSQL Database**  
   Once the matches data is downloaded to the local folder, it is inserted into the PostgreSQL database using `load_matches_data_into_postgres_from_folder` from `module_postgres.py`.

3. **Download Lineups and Events Data**  
   After storing the match data, lineups and events data is retrieved from the GitHub repository using `get_github_data_from_matches` from `module_github.py`.

#### Detailed Method Descriptions

##### `download_data_from_github_repo(repo_owner, repo_name, data_type, local_folder)`

- **Purpose:** Downloads data from a specific GitHub repository and stores it in a local folder.
- **Parameters:**
  - `repo_owner` (str): The owner of the repository (e.g., 'statsbomb').
  - `repo_name` (str): The name of the repository (e.g., 'open-data').
  - `data_type` (str): The type of data to download (e.g., 'matches', 'lineups', 'events').
  - `local_folder` (str): The local folder where the data will be saved.
- **Process:**
  1. Connects to the GitHub repository using the provided credentials.
  2. Downloads the specified data type.
  3. Stores the downloaded data in the provided local folder.

##### `load_matches_data_into_postgres_from_folder(local_folder)`

- **Purpose:** Loads the downloaded matches data from the local folder into a PostgreSQL database.
- **Parameters:**
  - `local_folder` (str): The path to the folder where the matches data is stored locally.
- **Process:**
  1. Connects to the PostgreSQL database.
  2. Reads the downloaded match files.
  3. Inserts the data into the appropriate database tables.

##### `get_github_data_from_matches(repo_owner, repo_name, data_type, local_folder)`

- **Purpose:** Downloads additional data (such as lineups or events) from the GitHub repository based on the matches stored in the PostgreSQL database.
- **Parameters:**
  - `repo_owner` (str): The owner of the repository.
  - `repo_name` (str): The name of the repository.
  - `data_type` (str): The type of data to download (e.g., 'lineups', 'events').
  - `local_folder` (str): The local folder where the downloaded data will be saved.
- **Process:**
  1. Connects to the GitHub repository.
  2. Downloads the required data based on the stored match data.
  3. Saves the data to the specified local folder.

### Loading Data into PostgreSQL from Local Folder

This script (`02-load_data_into_postgres_from_local.py`) is responsible for loading events and lineups data from a local folder into a PostgreSQL database. It assumes that the matches data was already loaded in a previous step, and focuses on events, lineups, and building the `events_details` table efficiently.

#### Process Overview

1. **Load Events Data into PostgreSQL:**  
   The method `load_events_data_into_postgres` is used to load the events data from the local folder into the PostgreSQL database.

2. **Load Lineups Data into PostgreSQL:**  
   The method `load_lineups_data_into_postgres` loads the lineups data from the local folder into the database.

3. **Load `events_details` Table Using SQL Script:**  
   The `events_details` table is built using a dedicated SQL script (`tables_setup_load_events_details_from_postgres.sql`). This step leverages PostgreSQL’s JSON functions for efficient data transformation directly within the database, avoiding row-by-row transfers.

#### Detailed Method Descriptions

##### `load_events_data_into_postgres(local_folder)`

- **Purpose:** Loads the events data from the local folder into the PostgreSQL database.
- **Parameters:**
  - `local_folder` (str): The path to the folder containing the downloaded events data.
- **Process:**
  1. Connects to the PostgreSQL database.
  2. Reads the events data from the local folder.
  3. Inserts the events data into the appropriate PostgreSQL table.

##### `load_lineups_data_into_postgres(local_folder)`

- **Purpose:** Loads the lineups data from the local folder into the PostgreSQL database.
- **Parameters:**
  - `local_folder` (str): The path to the folder containing the downloaded lineups data.
- **Process:**
  1. Connects to the PostgreSQL database.
  2. Reads the lineups data from the local folder.
  3. Inserts the lineups data into the appropriate PostgreSQL table.

##### Loading Data into `events_details` Table

For efficiency, as previous step loaded `events` data into the database, it is more efficient to INSERT FROM SELECT vs row by row INSERT.

This SQL script is designed to load event details from the `events` table into the `events_details` table in a PostgreSQL database. It processes each record in the `events` table, extracts relevant fields from a JSON structure, and inserts them into `events_details`.

1. **Cursor Declaration:**  
   A cursor (`cur`) is declared to fetch records from the `events` table.

2. **Loop to Process Records:**  
   The script loops through each record retrieved by the cursor and extracts the event details stored in a JSON field.

3. **Insertion into `events_details`:**  
   For each record, the following fields are inserted into `events_details`:
   - `match_id`
   - `id_guid` (extracted from the JSON field `data->>'id'`)
   - `index`, `period`, `timestamp`, `minute`, `second`
   - `type_id` and `type` (extracted from the JSON field `data->'type'`)
   - `possession`, `possession_team_id`, `possession_team`
   - `play_pattern_id` and `play_pattern`
   - The entire JSON object (`json_`)

4. **Logging the Process:**  
   After each insertion, a `RAISE NOTICE` statement is triggered, which prints the processed `match_id` and the total number of records inserted for that match.

### Load data from local Postgres to Azure Postgres PaaS Flexible

Before loading the data into Postgres PaaS Flexible, you need to setup the database in Azure.
Some tips:

- make sure your ISP don't block the port 5432, that is the default por for Postgres.
- you cannot change the default port in PaaS Postgres (not allowed in server configuration portal). TODO: test is from Azure Cli.
- add your public IP to the firewall rules in Postgres instance configuration.

In this project, we are using these extensions:

- vector
- azure_ai
- azure_local_ai

that requires this machine configuration:
"memory-optimized Azure VM SKUs with a minimum of 4 vCores. Today, if you are using a VM that does
not meet the minimum requirements, the azure_local_ai extension will not appear in the list of
available extensions in Server parameters"

Aditionally, the azure_local_ai, extension, as of today is only available in these regions:

- Australia East
- East USA
- France Central **
- Japan East
- UK South
- West Europe
- West USA
-

<https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/azure-local-ai>

these links have helped us to understand and install the requirements:

- <https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/generative-ai-azure-overview>
- <https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-extensions>
- <https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-extensions>

Note. In some cases, you might need to change the configuration parameters for the postgres inscance using azure cli:

<https://learn.microsoft.com/en-us/cli/azure/postgres/flexible-server?view=azure-cli-latest>

this will help you:

```bash

az postgres flexible-server parameter set `
    --resource-group <rg>  `
    --server-name <server> `
    --subscription <subs_id> `
    --name azure.extensions `
    --value vector,azure_ai,azure_local_ai


az postgres flexible-server update `
--name <dbname> `
--resource-group <rgname> `
--admin-password <password> `
```

After setting up the instance, you need to enable the extensions, and the endpoint to Azure AI. Use the following:

``` sql
-- azure_ai

CREATE EXTENSION azure_ai;
CREATE EXTENSION vector;

select azure_ai.set_setting('azure_openai.endpoint','https://<endpoint>.openai.azure.com'); 
select azure_ai.set_setting('azure_openai.subscription_key', 'key');

select azure_ai.get_setting('azure_openai.endpoint');
select azure_ai.get_setting('azure_openai.subscription_key');
select azure_ai.version();

ALTER EXTENSION azure_ai UPDATE;
ALTER EXTENSION vector UPDATE;


-- azure_local_ai

SELECT * FROM pg_available_extensions where name like '%vector%' or  name like '%azure%';

SHOW azure.extensions;

CREATE EXTENSION azure_local_ai;
CREATE EXTENSION vector;

SELECT azure_local_ai.get_setting('intra_op_parallelism');
SELECT azure_local_ai.get_setting('inter_op_parallelism');
SELECT azure_local_ai.get_setting('spin_control');

ALTER EXTENSION azure_local_ai UPDATE;
ALTER EXTENSION vector UPDATE;

```

If you need deep dive into the setup procedure, use the script setup_postgres-doc-resources.sql, located in the postges folder [filename](./postgres/setup_postgres-doc-resources.sql).

After configuring the server, run the script tables_setup_azure_local_ai.sql, in postgres folder, that create the relevent tables in postgres Azure [filename](./postgres/tables_setup_azure_local_ai.sql).

Now, you can run the phyton script: 03-load_tables_from_local_to_postgres_azure.py located in the python folder. [filename](./python/03-load_tables_from_local_to_postgres_azure.py).

## Start the application (streamlit)

```bash
python -m streamlit run main.py
streamlit hello
```

## Modules description

| **Module Name**           | **Purpose**                                                                 | **Functions**                                                                                                    |
|---------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| `module_github.py`         | Interacts with GitHub API to retrieve repository data and download files.   | `get_json_list_from_repo`, `download_file_from_repo_url`, `download_data_from_github_repo`, `get_github_data_from_matches` |
| `module_azureopenai.py`    | Connects to Azure OpenAI API for text generation, token management, and data retrieval. | `get_chat_completion_from_azure_open_ai`, `count_tokens`, `get_tokens_statistics_from_table_column`, `create_and_download_detailed_match_summary`, `get_top_n_results_from_summary_column`, `get_dataframe_from_ids`, `get_game_result_data`, `get_game_players_data` |
| `module_postgres.py`       | Handles PostgreSQL database operations including data transfer and processing match information. | `copy_data_from_postgres_to_azure`, `load_lineups_data_into_postgres`, `import_json_to_db`, `get_manager_info`, `get_json_events_details_from_match_id`, `download_match_script` |

### Module: module_github.py

#### `get_json_list_from_repo(repo_owner, repo_name, dataset)`

Retrieves a list of JSON files from a GitHub repository by traversing the first-level subdirectories.

- **Parameters:**
  - `repo_owner (str)`: The owner of the GitHub repository.
  - `repo_name (str)`: The name of the GitHub repository.
  - `dataset (str)`: The dataset directory within the repository.
- **Returns:** `pandas.DataFrame`: A DataFrame containing the dataset, subdirectory, and URL of each JSON file.

#### `download_file_from_repo_url(url, path, dir, subdir)`

Downloads a file from a given URL and saves it in the specified local path.

- **Parameters:**
  - `url (str)`: The URL of the file to download.
  - `path (str)`: The destination directory path.
  - `dir (str)`: The name of the directory.
  - `subdir (str)`: The name of the subdirectory.
- **Returns:** None. It prints the result of the download process.

#### `download_data_from_github_repo(repo_owner, repo_name, dataset_name, local_folder)`

Downloads data from a GitHub repository for the specified dataset and saves it to the local folder while preserving the repository structure.

- **Parameters:**
  - `repo_owner (str)`: The owner of the GitHub repository.
  - `repo_name (str)`: The name of the GitHub repository.
  - `dataset_name (str)`: The name of the dataset.
  - `local_folder (str)`: The local folder to save the files.
- **Returns:** None.

#### `get_github_data_from_matches(repo_owner, repo_name, dataset_name, local_folder)`

Retrieves data from GitHub related to match datasets and stores it in the specified local folder.

- **Parameters:** Various arguments related to the GitHub repository and dataset.
- **Returns:** None.

## Module: module_azureopenai.py

#### `get_chat_completion_from_azure_open_ai(system_message, user_prompt, temperature, tokens)`

Retrieves a chat completion from Azure OpenAI API.

- **Parameters:**
  - `system_message (str)`: The system message.
  - `user_prompt (str)`: The user prompt.
  - `temperature (float)`: The temperature value for generating chat completions.
  - `tokens (int)`: The maximum number of tokens for generating chat completions.
- **Returns:** `str`: The generated chat completion.

#### `count_tokens(prompt)`

Counts the number of tokens in the given prompt.

- **Parameters:** `prompt (str)`: The prompt to count tokens from.
- **Returns:** `int`: The number of tokens in the prompt.

### `get_tokens_statistics_from_table_column(source, table_name, column_name, filter, num_rows)`

Retrieves statistics about tokens in a specified table from the database.

- **Parameters:**
  - `source (str)`: The database source ("azure" or others).
  - `table_name (str)`: The name of the table.
  - `column_name (str)`: The name of the column to retrieve data from.
  - `filter (str)`: The filter condition for the query.
  - `num_rows (int)`: The number of rows to retrieve.
- **Returns:** `dict`: Token statistics, including total rows, mean, median, and standard deviation of tokens.

#### `create_and_download_detailed_match_summary(match_id, rows_per_prompt, file_prompt_size, temperature, system_message, tokens, local_folder)`

Generates a detailed match summary by splitting a match into multiple prompts and downloading the summary to a file.

- **Parameters:** Various arguments related to the match, prompt size, and temperature for generating the summary.
- **Returns:** None.

#### `get_top_n_results_from_summary_column(source, table_name, column_name, top_n, search_term, system_message, temperature, input_tokens, output_tokens)`

Fetches the top `n` results from the summary column based on the search term and other parameters.

- **Parameters:** Various arguments related to the source, table, and search term.
- **Returns:** A tuple with the prompt and the summary of the search results.

#### `get_dataframe_from_ids(source, table_name, summary, ids)`

Retrieves a DataFrame from the database using the given source, table name, summary column, and a list of IDs.

- **Parameters:**
  - `source (str)`: The source of the data (either "azure" or other).
  - `table_name (str)`: The table name.
  - `summary (str)`: The summary column to query.
  - `ids (list)`: A list of IDs to filter the query.
- **Returns:** `pandas.DataFrame`: The resulting DataFrame.

#### `get_game_result_data(source, match_id)`

Fetches game result data for a specific match from the database.

- **Parameters:**
  - `source (str)`: The source of the data ("azure" or other).
  - `match_id (int)`: The match ID.
- **Returns:** `str`: The game result data.

#### `get_game_players_data(source, match_id)`

Retrieves player data for a specific match from the database.

- **Parameters:**
  - `source (str)`: The source of the data ("azure" or other).
  - `match_id (int)`: The match ID.
- **Returns:** `str`: The player data.

## Module: module_postgres.py

#### `copy_data_from_postgres_to_azure(table_name, columns_list, match_id)`

Connects to a local PostgreSQL database and transfers data to an Azure PostgreSQL database.

- **Parameters:**
  - `table_name (str)`: The name of the table to copy data from.
  - `columns_list (str)`: A list of column names to transfer.
  - `match_id (int)`: The match ID to filter the data. If `<= 0`, all data will be copied.
- **Returns:** None. Outputs feedback on the data transfer process, including rows copied.

#### `load_lineups_data_into_postgres(local_folder)`

Imports lineup data from JSON files into the PostgreSQL database.

- **Parameters:** `local_folder (str)`: The directory path containing the lineup JSON files.
- **Returns:** None. Provides feedback on the number of records processed and inserted.

#### `import_json_to_db(folder_name)`

Processes match data from JSON files and stores it in the PostgreSQL database.

- **Parameters:** `folder_name (str)`: The folder containing the match JSON files.
- **Returns:** None. Outputs information about the matches inserted into the database.

#### `get_manager_info(managers)`

Retrieves detailed information about football managers from the database.

- **Parameters:** `managers (str)`: The manager(s) to retrieve information for.
- **Returns:** None.

#### `get_json_events_details_from_match_id(match_id)`

Retrieves event data for a specific match from the database.

- **Parameters:** `match_id (str)`: The ID of the match to retrieve.
- **Returns:** `pandas.DataFrame`: A DataFrame containing the match event details.

#### `download_match_script(source, table_name, match_id, column_name, local_folder, minutes_chunks)`

Downloads a match script from the PostgreSQL database, splitting it into chunks based on minutes.

- **Parameters:** Various arguments related to the match and table structure.
- **Returns:** None. The script is saved to the specified local folder.

Run the script:

```bash
python main.py
```

main.py includes comments.
Python code has different methods, each for a specific purpose:

Methods are:

- module_github
  - download_data_from_github_repo
  - get_github_data_from_matches

- module_postgres
  - copy_data_from_postgres_to_azure
  - download_match_script
  - load_matches_data_into_postgres_from_folder
  - load_lineups_data_into_postgres
  - load_events_data_into_postgres

- module_azureopenai
  - create_and_download_detailed_match_summary
  - create_events_summary_from_json_rows_in_database
  - create_match_summary
  - get_tokens_statistics_from_table_column

see coments in the .py files, and methods.

All methods that acess database, assumes that .env environments are used.
See the .env.example file.

This script performs various operations related to downloading, storing, and summarizing football match data.
The script follows the following steps:

  1. Download all matches data from a GitHub repository to a local folder.
  2. Store the downloaded matches data into a PostgreSQL database.
  3. Get lineups and events data from the GitHub repository based on the matches stored in the database.
  4. Load the downloaded data into PostgreSQL from the local folder.
  5. Copy data from the local PostgreSQL database to an Azure database.
  6. Convert each row of JSON data into a prose script.
  7. Create a detailed match summary based on the summaries of each event.
  8. Create a summary of the match using OpenAI API.
  9. Download the scripts in minute chunks from the database.
  10. Get token statistics from a table column.

Please note that this script requires environment variables to be set for various parameters such as repository owner, repository name, local folder path, database server, database name, database username, database password, and Azure database server, database name, username, and password.
The script is divided into several functions, each performing a specific task. The main function is executed when the script is run as a standalone program.
For more details on each step and the parameters used, please refer to the comments in the code.

## Example results

Euro Final: Spain 2 - England 1.

<https://www.uefa.com/euro2024/match/2036211--spain-vs-england/>

<https://www.youtube.com/watch?v=e1wdwgpEhdo>

```bash

content = """
        Make a summary of the match. 
        Include the game result, and most relevant actions such as goals, penalties, and injuries, and cards only if players are sent off. 
        Do not invent any information, relate stick to the data. 
        Relate in prose format the goals.
        Include two sections: data relevant for analysis, and a brief description of the match in prose format: 
        """

summary = match_summary(server_azure, database_azure, username_azure, password_azure, "final_match_Spain_England_events_details__minutewise", 3943043,
                        openai_endpoint, openai_key, "gpt-4o-mini", 0.1, 15000, content)

print(summary)


```

### Match Summary

**Result:** Spain 2 - 1 England
In a tightly contested match, Spain emerged victorious against England with a score of 2-1. The match featured a series of dynamic plays and tactical maneuvers from both teams.
In a tightly contested match, Spain emerged victorious against England with a score of 2-1. The match featured a series of dynamic plays and tactical maneuvers from both teams.

**Goals:**

- **Spain:**
  - **Nicholas Williams** scored the opening goal in the 46th minute, capitalizing on a swift passing sequence that culminated in a well-placed shot past England's goalkeeper, Jordan Pickford.
  - **Mikel Oyarzabal** doubled Spain's lead in the 75th minute with a precise shot after receiving a pass from Daniel Olmo, showcasing Spain's fluid attacking play.

- **England:**
  - **Cole Palmer** pulled one back for England in the 72nd minute, scoring with a deflected shot that found its way into the net, highlighting England's resilience and ability to capitalize on opportunities.
**Key Actions:**
- **Injuries:** Both Fabián Ruiz (Spain) and Kobbie Mainoo (England) suffered injuries in the 25th minute, leading to brief stoppages in play.
  - **Cole Palmer** pulled one back for England in the 72nd minute, scoring with a deflected shot that found its way into the net, highlighting England's resilience and ability to capitalize on opportunities.
**Key Actions:**
- **Cards:** John Stones received a yellow card in the 53rd minute for a foul on Martín Zubimendi.

### Data Relevant for Analysis

- **Possession:** Spain dominated possession throughout the match, particularly in the first half, where they held 79% possession at one point.
- **Shots on Goal:** Spain had multiple attempts on goal, with notable shots from Olmo and Yamal, while England's Foden and Bellingham also tested Spain's goalkeeper, Unai Simón.
- **Defensive Actions:** Both teams displayed strong defensive efforts, with Spain's Laporte and Carvajal making crucial clearances, while England's Guehi and Shaw effectively disrupted Spain's attacking flow.

### Match Description

The match began with both teams showcasing their tactical prowess, with Spain focusing on maintaining possession through short passes and quick transitions. England applied pressure, attempting to regain control and create scoring opportunities. The first half saw Spain's dominance in possession, but England's defensive resilience kept the scoreline level.
As the second half commenced, Spain quickly took the lead with a well-executed goal from Nicholas Williams. England responded with determination, and Cole Palmer's goal reignited their hopes. However, Spain's attacking fluidity proved too much for England, culminating in Oyarzabal's decisive strike.
Despite England's late attempts to equalize, Spain's defense held firm, securing a hard-fought victory. The match highlighted the tactical battle between the two teams, with Spain's possession-based approach ultimately prevailing over England's counter-attacking strategy.

## Usage of vector databases in SQL PaaS

- feature: <https://github.com/Azure-Samples/azure-sql-db-vector-search>
- requirements: <https://github.com/Azure-Samples/azure-sql-db-vector-search?tab=readme-ov-file#prerequisites>
- sign up: <https://aka.ms/azuresql-vector-eap>

## Data distribution

This script is in [tables_data_distribution](.\postgres\tables_data_distribution.sql)

### competitions by country/region

```sql
select competition_country, count(distinct season_name) seasons
from matches m
group by competition_country
order by seasons DESC limit 10;
```

![alt text](images/image.png)

### competitions by country/region

```sql
select competition_country, count(distinct competition_name) competitions
from matches m
group by competition_country
order by competitions DESC limit 10;
```

![alt text](images/image-1.png)

### seasons by country/region

```sql
select distinct competition_country, season_name
from matches m
order by competition_country limit 10;
```

![alt text](images/image-2.png)

### seasons by country/region

```sql
select distinct competition_country, season_name
from matches m
order by season_name limit 10;
```

![alt text](images/image-3.png)

### recent season by country/region

```sql
select competition_country, competition_name, season_name, count(*) matches
group by competition_country, competition_name, season_name
order by season_name DESC limit 15;
```

![alt text](images/image-4.png)
