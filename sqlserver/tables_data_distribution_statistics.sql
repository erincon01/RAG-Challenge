/*
This SQL script retrieves various statistics related to competitions and seasons by country/region from the "matches" table.

1. Competitions by Country/Region:
    - Retrieves the number of distinct seasons for each competition country/region.
    - The result is ordered by the number of seasons in descending order.
    - The limit is set to 10.

2. Competitions by Country/Region:
    - Retrieves the number of distinct competitions for each competition country/region.
    - The result is ordered by the number of competitions in descending order.
    - The limit is set to 10.

3. Seasons by Country/Region:
    - Retrieves the distinct competition country/region and season name from the "matches" table.
    - The result is ordered by the competition country/region.
    - The limit is set to 10.

4. Seasons by Country/Region:
    - Retrieves the distinct competition country/region and season name from the "matches" table.
    - The result is ordered by the season name.
    - The limit is set to 10.

5. Recent Season by Country/Region:
    - Retrieves the competition country/region, competition name, season name, and the count of matches for each combination.
    - The result is grouped by competition country/region, competition name, and season name.
    - The result is ordered by the season name in descending order.
    - The limit is set to 15.
*/

-- competitions by country/region
select top 10 competition_country, count(distinct season_name) seasons
from matches m
group by competition_country
order by seasons DES;

-- competitions by country/region
select top 10 competition_country, count(distinct competition_name) competitions
from matches m
group by competition_country
order by competitions DESC;

-- seassons by country/region
select top 10 distinct competition_country, season_name
from matches m
order by competition_country;

select top 10 distinct competition_country, season_name
from matches m
order by season_name;

-- recent season by country/region
select top 15 competition_country, competition_name, season_name, count(*) matches
from matches m
group by competition_country, competition_name, season_name
order by season_name DESC;

