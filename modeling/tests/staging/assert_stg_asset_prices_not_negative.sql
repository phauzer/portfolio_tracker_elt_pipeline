SELECT
    price
FROM   
    {{ref('stg_asset_prices')}}
WHERE price < 0