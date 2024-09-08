# statsbomb-loader
statsbomb loader

- Load data from https://github.com/statsbomb/open-data into postgres.

- WIP for Microsoft RAG challenge:
https://github.com/microsoft/RAG_Hack?tab=readme-ov-file#raghack-lets-build-rag-applications-together

- Official event: https://reactor.microsoft.com/es-es/reactor/events/23332/


## Install dependencies:

```bash
pip install -r requirements.txt
```

## Configure environment variables:

Fill in the .env file with your data. see .env.example file.

```bash
    # Base URL to access data on GitHub
BASE_URL=https://github.com/statsbomb/open-data/raw/master/data

REPO_OWNER=statsbomb
REPO_NAME=open-data
LOCAL_FOLDER=./data

# Configuración de la base de datos
DB_SERVER=your_server_name.database.windows.net
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
```

Run the script:

```bash
python main.py
```

main.py includes comments.
Python code has different methods, each for a specific purpose:

Methods are:

- module_azureopenai
  - get_events_from_database
  - get_script
  - get_tokens_statistics
- module_github
  - download_file_from_repo_url
  - download_data_from_github_repo
  - get_github_data_from_matches
  - get_json_list_from_repo
- module_postgres
  - convert_json_to_summary
  - copy_data_from_postgres_to_azure
  - export_match_summary_minutes
  - get_match_summary_from_azure_openai
  - load_lineups_data_into_postgres
  - load_events_data_into_postgres
  - load_matches_data_into_postgres


see coments in the .py files, and methods.

All methods that acess database, assumes that .env environments are used.
See the .env.example file.


```bash


    # 1) download all matches data from GitHub repository (statsbomb) to local folder
    download_data_from_github_repo(repo_owner, repo_name, "matches", local_folder)

    # 2) store into the database the matches data
    load_matches_data_into_postgres(local_folder)

    # 3) get lineups and events data, based on the matches stored in the database. 
    #    this method only downloads the data from the repository into the local folder.
    #    it does not store the data into the database.
    get_github_data_from_matches(repo_owner, repo_name, "lineups", local_folder)
    get_github_data_from_matches(repo_owner, repo_name, "events", local_folder)


    # 4) load downloadded data into PostgreSQL from local folder
    load_lineups_data_into_postgres(local_folder)
    load_events_data_into_postgres(local_folder)

    # 5) copy data from local to azure

    # matches table
    table_name = "matches"
    table_columns = "match_id, match_date, competition_id, competition_country, competition_name, season_id, season_name, home_team_id, home_team_name, home_team_gender, home_team_country, home_team_manager, home_team_manager_country, away_team_id, away_team_name, away_team_gender, away_team_country, away_team_manager, away_team_manager_country, home_score, away_score, result, match_week, stadium_id, stadium_name, stadium_country, referee_id, referee_name, referee_country, json_"
    copy_data_from_postgres_to_azure(server_azure, database_azure, username_azure, password_azure,
                                  table_name, table_columns)

    # lineups table
    table_name = "lineups"
    table_columns = "match_id, home_team_id, home_team_name, away_team_id, away_team_name, json_"
    copy_data_from_postgres_to_azure(server_azure, database_azure, username_azure, password_azure,
                                  table_name, table_columns)

    # players table
    table_name = "players"
    table_columns = "match_id, team_id, team_name, player_id, player_name, jersey_number, country_id, country_name, position_id, position_name, from_time, to_time, from_period, to_period, start_reason, end_reason"
    copy_data_from_postgres_to_azure(server_azure, database_azure, username_azure, password_azure,
                                  table_name, table_columns)

    # events table
    table_name = "events"
    table_columns = "match_id, json_"
    copy_data_from_postgres_to_azure(server_azure, database_azure, username_azure, password_azure,
                                  table_name, table_columns)

    # # events_details table
    # this table is loaded using the script /postgres/tables_setup_load_events_details_from_postgres.sql
    # reason is because it is more efficient to build the data using json functions in postgres vs trasnferring the data row by row


    # For azure_open_ai or azure_local_ai
    #     model = "azure_local_ai"  # azure_open_ai,
    #     ### azure_local_ai (see azure_open_ai documentation, only supported in specific regions and Memory Optimized, E4ds_v5, 4 vCores, 32 GiB RAM, 128 GiB storage)

    convert_json_to_summary(server_azure, database_azure, username_azure, password_azure, "final_match_Spain_England_events_details__minutewise", 3943043,
                            openai_endpoint, openai_key, "gpt-4o-mini", 0.1, 8000, content)

    
    content = """
            Make a summary of the match. 
            Include the game result, and most relevant actions such as goals, penalties, and injuries, and cards only if players are sent off. 
            Do not invent any information, relate stick to the data. 
            Relate in prose format the goals.
            Include two sections: data relevant for analysis, and a brief description of the match in prose format: 
            """

    match_id = 3943043
    summary = match_summary(server_azure, database_azure, username_azure, password_azure, "final_match_Spain_England_events_details__minutewise", match_id,
                          openai_endpoint, openai_key, "gpt-4o-mini", 0.1, 15000, content)
    
    folder = os.path.join(local_folder, "scripts_summary")
    filename = f"summary_{match_id}.txt"

    with open(os.path.join(local_folder, folder, filename), "w", encoding="utf-8") as f:
        f.write(summary)
    print(summary)
     
    export_match_summary_minutes(server_azure, database_azure, username_azure, password_azure, "final_match_Spain_England_events_details__minutewise", 3943043, folder, 10)

    s = get_tokens_statistics(server_azure, database_azure, username_azure, password_azure, "final_match_Spain_England_events_details__minutewise", -1)
    print (s)

    s = get_tokens_statistics(server_azure, database_azure, username_azure, password_azure, "events_details", -1)
    print (s)


   
```

## Example results

Euro Final: Spain 2 - England 1.

https://www.uefa.com/euro2024/match/2036211--spain-vs-england/

https://www.youtube.com/watch?v=e1wdwgpEhdo


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



## Usage of vector databases in SQL PaaS:

- feature: https://github.com/Azure-Samples/azure-sql-db-vector-search
- requirements: https://github.com/Azure-Samples/azure-sql-db-vector-search?tab=readme-ov-file#prerequisites
- sign up: https://aka.ms/azuresql-vector-eap


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

