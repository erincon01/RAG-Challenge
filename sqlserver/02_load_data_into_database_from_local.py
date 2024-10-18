import os
"""
This script loads events and lineups data into a SQL Server database from a local folder.
Parameters:
- repo_owner (str): The owner of the repository where the data is stored.
- repo_name (str): The name of the repository where the data is stored.
- local_folder (str): The path to the local folder containing the data.
Steps:
1. Load events data into the SQL Server database.
2. Load lineups data into the SQL Server database.
3. Load events_details table using the script /postgres/tables_setup_load_events_details_from_sql_paas.sql.
Note: The matches data is not necessary to load again as it was already loaded in step 01.
Usage:
- Set the environment variables LOCAL_FOLDER to the appropriate values.
- Run the script.
"""
from module_data import load_events_data_into_sql_paas, load_lineups_data_into_sql_paas, copy_data_between_sql_sources, create_tables_sqlite

if __name__ == "__main__":

    # Local folder
    local_folder = os.getenv('LOCAL_FOLDER')

    # 1) Load events data into SQL Server database
    load_events_data_into_sql_paas("azure-sql", local_folder)

    # 2) Load lineups data into SQL Server database
    load_lineups_data_into_sql_paas("azure-sql", local_folder)

    # 3) Load events_details table using the script
    # This table is loaded using the script /sqlserver/tables_setup_load_events_details_from_sql_paas.sql
    # It is more efficient to build the data using JSON functions in SQL rather than transferring the data row by row

    # OPTIONAL: Pull SQL PaaS data to SQLite locally
    # It may not make much sense to upload the data to Azure and then download it locally,
    # but this is an alternative for someone who wants to explore data locally

    # # 2b) OPTIONAL: Create tables in SQLite database
    # source_file = os.path.join("sqlserver", "00b_tables_setup_sqlite_optional.sql")
    # create_tables_sqlite("sqlite", source_file)
    # source_file = os.path.join("sqlserver", "00c_tables_setup_sqlite_optional_agg.sql")
    # create_tables_sqlite("sqlite", source_file)

    # # Copy data between SQL sources
    # copy_data_between_sql_sources("azure-sql", "sqlite", "matches", "match_id,match_date,competition_id,competition_country,competition_name,season_id,season_name,home_team_id,home_team_name,home_team_gender,home_team_country,home_team_manager,home_team_manager_country,away_team_id,away_team_name,away_team_gender,away_team_country,away_team_manager,away_team_manager_country,home_score,away_score,result,match_week,stadium_id,stadium_name,stadium_country,referee_id,referee_name,referee_country,json_")

    # filter = "match_id IN (SELECT match_id FROM matches)"
    # copy_data_between_sql_sources("azure-sql", "sqlite", "lineups", "match_id,home_team_id,home_team_name,away_team_id,away_team_name,json_", filter)
    # copy_data_between_sql_sources("azure-sql", "sqlite", "players", "match_id,team_id,team_name,player_id,player_name,jersey_number,country_id,country_name,position_id,position_name,from_time,to_time,from_period,to_period,start_reason,end_reason", filter)
    # copy_data_between_sql_sources("azure-sql", "sqlite", "events", "match_id,json_", filter)
    # copy_data_between_sql_sources("azure-sql", "sqlite", "events_details", "[match_id], [id_guid], [index_], [period], [timestamp], [minute], [second], [type_id], [type], [possession], [possession_team_id], [possession_team], [play_pattern_id], [play_pattern], [json_]", filter)

    # filter = "match_id IN (SELECT match_id FROM matches)"
    # copy_data_between_sql_sources("azure-sql", "sqlite", "events_details__15secs_agg", "[match_id], [period], [minute], [_15secs], [count], [json_], [summary]", filter)
    # copy_data_between_sql_sources("azure-sql", "sqlite", "events_details__minute_agg", "[match_id], [period], [minute], [count], [json_], [summary]", filter)
