SELECT
    ticker,
    SUM(amount)
FROM
    {{ref('stg_transactions')}}
GROUP BY 1
HAVING SUM(amount) < 0