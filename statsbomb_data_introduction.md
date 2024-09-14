## Competitions

The competitions table in the StatsBomb Open Competitions Specification (v2.0.0) contains data in `JSON` format, which represents an array of `competition`-season objects. Each object consists of key properties that describe various details about the competition, such as `competition_id` (a unique identifier), `season_id`, `competition_name`, and `competition_gender`. These attributes provide essential information for identifying and distinguishing different competitions and seasons within the dataset.

Additionally, the table includes the `country_name`, which specifies the country or region that the competition is related to, and the `season_name`, indicating the name of the corresponding season. Two other key fields are match_updated, which captures the date and time when a match in that competition and season was last updated, and `match_available`, which records when a match was made available or last updated.

## Matches

The Matches table from the StatsBomb Open Matches Specification (v3.0.0) provides detailed information about individual football matches in `JSON` format. Each match is represented as an object containing key attributes such as match_id, a unique identifier, and information about the competition (`competition_id` and `competition_name`) and season (`season_id` and `season_name`). It also includes details on the date and time of the match (match_date, kick_off), the stadium (`stadium_id` and `stadium_name`), and the teams involved (home_team and away_team with corresponding genders).

Additional information covers the final scores for both teams (home_score, away_score), the referee (`referee_name`), and match-specific data such as the status (match_status) and the week in the competition (`match_week`). There are also fields for when the match data was last updated (last_updated) and metadata related to the event data version and other tags for tracking purposes​

## Players

The Players table in the StatsBomb Open Lineups Specification (v2.0.0) provides detailed information about players involved in a match, presented in JSON format. Each player is identified by a unique `player_id` and accompanied by attributes such as `player_name`, `player_nickname`, and `jersey_number`. The player’s nationality is represented by a country object that includes both an ID and a name. This table is structured as part of the lineups data, which details the squad for both teams involved in the match​(Open Data Lineups v2.0.0).

Additionally, the players are listed in an array within the lineup variable, providing easy access to the full squad. This structure allows for detailed tracking of players' participation and roles within a match, supporting in-depth analytics for team and individual performance. This data is stored in files named after the match ID and can be used in various applications related to football data analysis​.

## Teams

The Teams table in the StatsBomb Open Matches Specification (v3.0.0) provides key information about the teams participating in a match. Each team is represented by a unique team_id and team_name. The table also includes attributes for the gender of the team (team_gender) and the country of origin, encapsulated in the team_country object, which provides both the country’s ID and name. This allows the identification and categorization of teams in terms of both geographic and gender distinctions​(Open Data Matches v3.0.0).

The teams are divided into home_team and away_team, with additional details for each team's manager (`manager_name`, `manager_nickname`, `manager_country`). The structure helps to analyze and compare team performance, player lineups, and coaching strategies. These team-related details are critical for understanding match dynamics and outcomes, providing valuable insights for football analytics​.

## Events

The Events table in the StatsBomb Open Events Specification (v4.0.0) outlines detailed in-game actions that occur during a football match. Each event is identified by a unique event_id and categorized by an event_type, which includes actions like passes, shots, tackles, and goals. Each event also contains the timestamp (the precise time the event occurred), as well as location, which provides the coordinates of the event on the pitch. Additional attributes like period, minute, and second specify when the event took place during the match​(Open Data Events v4.0.0).

Other important attributes include the team and player involved in the event, identified by team_id and player_id. Each event may also contain metadata such as whether it occurred "under pressure" or was a part of a specific play pattern (e.g., counter-attacks or set-pieces). This detailed event structure allows for complex analysis of match flow, player contributions, and tactical dynamics during a game​(Open Data Events v4.0.0).