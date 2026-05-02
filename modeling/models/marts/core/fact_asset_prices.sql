WITH prices AS 
(
    SELECT
        {{generate_date_id('date')}} as date_id,
        ticker,
        price AS asset_price
    FROM
        {{ref('stg_asset_prices')}}
),

tickers AS
(
    SELECT
        ticker_id,
        ticker
    FROM 
        {{ref('dim_assets')}}
),

all_dates AS
(
    SELECT
        date_id
    FROM
        {{ref('dim_date')}}
),

tickers_everyday AS
(
    SELECT
        date_id,
        ticker_id,
        ticker
    FROM
        all_dates 
        CROSS JOIN tickers
),

final_prices AS
(
    SELECT 
        t.date_id,
        t.ticker_id,
        LAST_VALUE(asset_price IGNORE NULLS) 
        OVER(PARTITION BY t.ticker ORDER BY t.date_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as asset_price
    FROM
        tickers_everyday AS t
        LEFT JOIN prices AS p
        ON  t.date_id = p.date_id
        AND t.ticker = p.ticker
),

final AS
(
    SELECT
        generate_uuid() AS asset_price_id,
        date_id,
        ticker_id,
        asset_price
    FROM
        final_prices
)

SELECT * FROM final