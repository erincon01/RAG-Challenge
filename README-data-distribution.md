## Data distribution

This script is in:
- Postgres: [tables_data_distribution_statistics](.\postgres\tables_data_distribution_statistics.sql)
- SQL Server: [tables_data_distribution_statistics](.\postgres\tables_data_distribution_statistics.sql)


### competitions by country/region

```sql
select competition_country, count(distinct season_name) seasons
from matches m
group by competition_country
order by seasons DESC;
```

![alt text](images/image.png)

### competitions count by country/region

```sql
select competition_country, count(distinct competition_name) competitions
from matches m
group by competition_country
order by competitions DESC;
```

![alt text](images/image-1.png)

### seasons by country/region

```sql
select distinct competition_country, season_name
from matches m
order by competition_country;
```

![alt text](images/image-2.png)

### seasons2 by country/region

```sql
select distinct competition_country, season_name
from matches m
order by season_name;
```

![alt text](images/image-3.png)

### recent season by country/region

```sql
select competition_country, competition_name, season_name, count(*) matches
group by competition_country, competition_name, season_name
order by season_name DESC;
```

![alt text](./images/image-4.png)
