WITH staging AS
(
SELECT 
    CAST(LEFT(REPLACE(`Date YYYY-MM-DD`,'.','-'),10) AS DATE) AS date,
    Ticker AS ticker,
    `Trade price use dot for decimal` AS trade_price,
    `Currency code` AS currency_code,
    `Amount + for buy - for sell` AS amount
FROM 
    {{source('portfolio', 'raw_transactions')}}
)

SELECT * FROM staging