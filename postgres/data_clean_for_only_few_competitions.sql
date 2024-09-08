

-- fist step: select the competitions for the dataset


-- recent season by country/region
select competition_id, season_id, competition_country, competition_name, season_name, count(*) matches
from matches m
where season_name in ('2020/2021', '2021/2022', '2022/2023', '2023/2024', '2022', '2023', '2024')
and competition_name in ('UEFA Euro', 'Copa America', 'FIFA World Cup')
group by competition_id, competition_country, competition_name, season_id, season_name
order by season_name DESC;

-- for example

/*

 competition_id,competition_country,competition_name,season_id,season_name,matches
 55,Europe,282,UEFA Euro,2024,51
 223,South America,282,Copa America,2024,32
 43,International,106,FIFA World Cup,2022,64


tables relations are:

matches contains: match_id, competition_id, competition_country, competition_name, season_name

matches (match_id) -> lineups
matches (match_id) -> players
matches (match_id) -> events 
matches (match_id) -> events_details

*/



-- cleaning data

delete from lineups where match_id not in (
    select distinct match_id
    from matches m
    where season_name in ('2020/2021', '2021/2022', '2022/2023', '2023/2024', '2022', '2023', '2024')
    and competition_name in ('UEFA Euro', 'Copa America', 'FIFA World Cup')
);


delete from players where match_id not in (
    select distinct match_id
    from matches m
    where season_name in ('2020/2021', '2021/2022', '2022/2023', '2023/2024', '2022', '2023', '2024')
    and competition_name in ('UEFA Euro', 'Copa America', 'FIFA World Cup')
);

delete from events where match_id not in (
    select distinct match_id
    from matches m
    where season_name in ('2020/2021', '2021/2022', '2022/2023', '2023/2024', '2022', '2023', '2024')
    and competition_name in ('UEFA Euro', 'Copa America', 'FIFA World Cup')
);

delete from events_details where match_id not in (
    select distinct match_id
    from matches m
    where season_name in ('2020/2021', '2021/2022', '2022/2023', '2023/2024', '2022', '2023', '2024')
    and competition_name in ('UEFA Euro', 'Copa America', 'FIFA World Cup')
);

delete from matches where match_id not in
 (
    select distinct match_id
    from matches m
    where season_name in ('2020/2021', '2021/2022', '2022/2023', '2023/2024', '2022', '2023', '2024')
    and competition_name in ('UEFA Euro', 'Copa America', 'FIFA World Cup')
);

select count(*) from lineups;
select count(*) from players;
select count(*) from events;
select count(*) from events_details;
select count(*) from matches;


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
group by competition_country, competition_name, season_name;


select competition_country, competition_name, season_name, count(*)
from matches m
group by competition_country, competition_name, season_name
order by 1;


