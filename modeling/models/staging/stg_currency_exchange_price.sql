WITH staging AS 
(
SELECT
    CAST(dates AS DATE) AS date, 
    currency_code,
    rate
FROM 
    {{source('portfolio', 'raw_currency_exchange_price')}}
)

SELECT * FROM staging