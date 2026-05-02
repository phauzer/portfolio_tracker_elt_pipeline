WITH currency_rates AS
(
    SELECT
        {{generate_date_id('date')}} AS date_id,
        currency_code,
        rate AS currency_rate
    FROM
        {{ref('stg_currency_exchange_price')}}
),

all_dates AS
(
    SELECT 
        date_id
    FROM 
        {{ref('dim_date')}}
),

currencies AS
(
    SELECT DISTINCT
        currency_code
    FROM
        {{ref('dim_assets')}}
),

currency_everyday AS
(
    SELECT
        date_id,
        currency_code
    FROM
        all_dates
        CROSS JOIN currencies
),

final_rates AS
(
    SELECT
        ce.date_id,
        ce.currency_code,
        LAST_VALUE(currency_rate IGNORE NULLS) 
        OVER(PARTITION BY ce.currency_code ORDER BY ce.date_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as currency_rate
    FROM
        currency_everyday AS ce
        LEFT JOIN currency_rates AS cr
        ON ce.date_id = cr.date_id
        AND ce.currency_code = cr.currency_code
),

final AS
(
    SELECT
        GENERATE_UUID() AS currency_rate_id,
        currency_code,
        currency_rate
    FROM final_rates
)

SELECT * FROM final