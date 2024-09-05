select type, count(*) c from events_details
group by type
order by c desc;

SELECT 
    COUNT(*) AS shoot,
    CASE
        WHEN CAST(minute AS INTEGER) BETWEEN 0 AND 4 THEN '00-04'
        WHEN CAST(minute AS INTEGER) BETWEEN 5 AND 9 THEN '05-09'
        WHEN CAST(minute AS INTEGER) BETWEEN 10 AND 14 THEN '10-14'
        WHEN CAST(minute AS INTEGER) BETWEEN 15 AND 19 THEN '15-19'
        WHEN CAST(minute AS INTEGER) BETWEEN 20 AND 24 THEN '20-24'
        WHEN CAST(minute AS INTEGER) BETWEEN 25 AND 29 THEN '25-29'
        WHEN CAST(minute AS INTEGER) BETWEEN 30 AND 34 THEN '30-34'
        WHEN CAST(minute AS INTEGER) BETWEEN 35 AND 39 THEN '35-39'
        WHEN CAST(minute AS INTEGER) BETWEEN 40 AND 44 THEN '40-44'
        WHEN CAST(minute AS INTEGER) BETWEEN 45 AND 49 THEN '45-49'
        WHEN CAST(minute AS INTEGER) BETWEEN 50 AND 54 THEN '50-54'
        WHEN CAST(minute AS INTEGER) BETWEEN 55 AND 59 THEN '55-59'
        WHEN CAST(minute AS INTEGER) BETWEEN 60 AND 64 THEN '60-64'
        WHEN CAST(minute AS INTEGER) BETWEEN 65 AND 69 THEN '65-69'
        WHEN CAST(minute AS INTEGER) BETWEEN 70 AND 74 THEN '70-74'
        WHEN CAST(minute AS INTEGER) BETWEEN 75 AND 79 THEN '75-79'
        WHEN CAST(minute AS INTEGER) BETWEEN 80 AND 84 THEN '80-84'
        WHEN CAST(minute AS INTEGER) BETWEEN 85 AND 89 THEN '85-89'
        ELSE '90+' -- Para cualquier minuto 90 o superior
    END AS minute_interval
FROM 
    events_details where type = 'Shot'
GROUP BY 
    minute_interval
ORDER BY 
    2;


SELECT 
    COUNT(*) AS goal,
    CASE
        WHEN CAST(minute AS INTEGER) BETWEEN 0 AND 4 THEN '00-04'
        WHEN CAST(minute AS INTEGER) BETWEEN 5 AND 9 THEN '05-09'
        WHEN CAST(minute AS INTEGER) BETWEEN 10 AND 14 THEN '10-14'
        WHEN CAST(minute AS INTEGER) BETWEEN 15 AND 19 THEN '15-19'
        WHEN CAST(minute AS INTEGER) BETWEEN 20 AND 24 THEN '20-24'
        WHEN CAST(minute AS INTEGER) BETWEEN 25 AND 29 THEN '25-29'
        WHEN CAST(minute AS INTEGER) BETWEEN 30 AND 34 THEN '30-34'
        WHEN CAST(minute AS INTEGER) BETWEEN 35 AND 39 THEN '35-39'
        WHEN CAST(minute AS INTEGER) BETWEEN 40 AND 44 THEN '40-44'
        WHEN CAST(minute AS INTEGER) BETWEEN 45 AND 49 THEN '45-49'
        WHEN CAST(minute AS INTEGER) BETWEEN 50 AND 54 THEN '50-54'
        WHEN CAST(minute AS INTEGER) BETWEEN 55 AND 59 THEN '55-59'
        WHEN CAST(minute AS INTEGER) BETWEEN 60 AND 64 THEN '60-64'
        WHEN CAST(minute AS INTEGER) BETWEEN 65 AND 69 THEN '65-69'
        WHEN CAST(minute AS INTEGER) BETWEEN 70 AND 74 THEN '70-74'
        WHEN CAST(minute AS INTEGER) BETWEEN 75 AND 79 THEN '75-79'
        WHEN CAST(minute AS INTEGER) BETWEEN 80 AND 84 THEN '80-84'
        WHEN CAST(minute AS INTEGER) BETWEEN 85 AND 89 THEN '85-89'
        ELSE '90+' -- Para cualquier minuto 90 o superior
    END AS minute_interval
FROM 
    events_details where type like 'Own Goal%'
GROUP BY 
    minute_interval
ORDER BY 
    2;


select count(*) from events_details where type like 'Own Goal%';

select *
from events_details limit 100;
