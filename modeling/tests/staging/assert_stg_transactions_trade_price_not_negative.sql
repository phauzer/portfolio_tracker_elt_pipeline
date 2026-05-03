SELECT
    trade_price
FROM
    {{ref('stg_transactions')}}
WHERE
    trade_price < 0