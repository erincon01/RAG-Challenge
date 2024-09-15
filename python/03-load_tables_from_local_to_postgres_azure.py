from module_postgres import copy_data_from_postgres_to_azure
"""
Copy data from local PostgreSQL database to Azure.
Args:
    table_name (str): The name of the table to copy data from.
    table_columns (str): The columns to copy from the table.
    data_filter (str): Optional filter to apply to the data.
Returns:
    None
"""

# 3) copy data from local to azure

##### France - Argentina match_id: 3869685
##### England - Spain match_id: 3943043

# matches table

data_filter =""
table_name = "matches"
table_columns = "match_id, match_date, competition_id, competition_country, competition_name, season_id, season_name, home_team_id, home_team_name, home_team_gender, home_team_country, home_team_manager, home_team_manager_country, away_team_id, away_team_name, away_team_gender, away_team_country, away_team_manager, away_team_manager_country, home_score, away_score, result, match_week, stadium_id, stadium_name, stadium_country, referee_id, referee_name, referee_country, json_"
copy_data_from_postgres_to_azure(table_name, table_columns, data_filter)

# lineups table

data_filter =""
table_name = "lineups"
table_columns = "match_id, home_team_id, home_team_name, away_team_id, away_team_name, json_"
copy_data_from_postgres_to_azure(table_name, table_columns, data_filter)

# players table

data_filter=""
table_name = "players"
table_columns = "match_id, team_id, team_name, player_id, player_name, jersey_number, country_id, country_name, position_id, position_name, from_time, to_time, from_period, to_period, start_reason, end_reason"
copy_data_from_postgres_to_azure(table_name, table_columns, data_filter)

# # events table

data_filter =""
table_name = "events"
table_columns = "match_id, json_"
copy_data_from_postgres_to_azure(table_name, table_columns, data_filter)
