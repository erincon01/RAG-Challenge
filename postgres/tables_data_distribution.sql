
-- competitions by country/region
select competition_country, count(distinct season_name) seasons
from matches m
group by competition_country
order by seasons DESC limit 10;

-- competitions by country/region
select competition_country, count(distinct competition_name) competitions
from matches m
group by competition_country
order by competitions DESC limit 10;

-- seassons by country/region
select distinct competition_country, season_name
from matches m
order by competition_country limit 10;

select distinct competition_country, season_name
from matches m
order by season_name limit 10;

-- recent season by country/region
select competition_country, competition_name, season_name, count(*) matches
from matches m
group by competition_country, competition_name, season_name
order by season_name DESC limit 15;

