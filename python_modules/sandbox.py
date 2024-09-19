import os
import json
import pandas as pd
import pyodbc
import sqlite3 as sqllib3
import psycopg2

from  module_data import get_competitions_summary_data, get_competitions_summary_with_teams_data, get_competitions_results_data, \
    get_all_matches_data, get_players_summary_data, get_teams_summary_data, get_events_summary_data, \
    get_competitions_summary_with_teams_and_season_data, get_tables_info_data, decode_source, get_connection, get_game_result_data
from module_azure_openai import search_details_using_embeddings, get_chat_completion_from_azure_open_ai, get_random_dataframe_from_match_id, get_dataframe_from_ids

print ("Start")


