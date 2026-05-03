SELECT
    rate
FROM   
    {{ref('stg_currency_exchange_rate')}}
WHERE rate < 0