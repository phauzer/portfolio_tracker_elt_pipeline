WITH alldate AS
(
    {{
        dbt_utils.date_spine(
            datepart="day",
            start_date="CAST('2000-01-01' AS DATE)",
            end_date="CAST('2100-01-01' AS DATE)"
        )
    }}
),

date_limits AS
(
    SELECT
        MIN(date) AS min_date,
        current_date() as max_date
    FROM 
        {{ref('stg_transactions')}}
),

limited_dates AS
(
    SELECT
        CAST(ad.date_day AS DATE) AS date
    FROM
        alldate AS ad
        CROSS JOIN date_limits AS dl
    WHERE
        ad.date_day >= min_date
        AND ad.date_day <= max_date
),

final AS
(
    SELECT
        CAST(REPLACE(CAST(date AS STRING),'-','') AS INTEGER) AS date_id,
        date,
        EXTRACT(YEAR FROM date) AS date_year,
        EXTRACT(MONTH FROM date) AS date_month,
        FORMAT_DATE('%B', date) AS date_month_name,
        EXTRACT(DAY FROM date) AS date_day,
        FORMAT_DATE('%A', date) AS date_weekday
    FROM
        limited_dates
)

SELECT * FROM final