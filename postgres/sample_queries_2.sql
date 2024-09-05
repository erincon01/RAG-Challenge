

-- data check
-- maches_data
select count(distinct match_id) from players;
select count(distinct match_id) from lineups;
select count(distinct match_id) from matches;
select count(distinct match_id) from events;
select count(distinct match_id) from events_details;

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
select competition_id, competition_country, competition_name, season_name, count(*) matches
from matches m
where season_name in ('2020/2021', '2021/2022', '2022/2023', '2023/2024', '2022', '2023', '2024')
and competition_name in ('UEFA Euro', 'Copa America', 'FIFA World Cup')
group by competition_id, competition_country, competition_name, season_name
order by season_name DESC;

-- events per competition
select competition_country, competition_name, season_name, 
count(*) events,
count(*)/count(distinct ed.match_id) events_per_match
from events_details ed
join matches m
on ed.match_id = m.match_id
where m.season_name in ('2020/2021', '2021/2022', '2022/2023', '2023/2024', '2022', '2023', '2024')
and m.competition_name in ('UEFA Euro', 'Copa America', 'FIFA World Cup')
group by competition_country, competition_name, season_name




select distinct competition_country, competition_name, season_name
from matches m
order by 1


