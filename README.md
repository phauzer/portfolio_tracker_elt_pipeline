# Cloud-Based Portfolio Tracker Pipeline
Automated end-to-end ELT data pipeline for tracking an EUR based portfolio value, separating asset and FX yield and insights over time.

## Business problem
Tracking an investment portfolio manually without insights can be troublesome and error-prone. This project wants to eliminate these problems by requiring only the new asset transactions loaded into a Google Sheet, then using a **Modern Data Stack** extract, load and transform the data before visualizing it.

**Explore the interactive dbt Documentation and Data Lineage [CLICK HERE](https://peti0505.github.io/portfolio_tracker_elt_pipeline/)**

## Architecture and Dataflow

<img width="836" height="405" alt="portolfio_elt_project" src="https://github.com/user-attachments/assets/852def34-cdd9-416f-afff-8ac5dce32f26" />

## Tech Stack

* **Data Sources**: Google Sheets API (gspread), Tiingo API, Frankfurter API
* **Extraction and Loading**: Python -> Pandas, Pandas_gbq, requests, comprehensive logging and error-handling
* **Data Warehouse**: Google BigQuery -> Cloud based DWH
* **Transformation and Modeling**: dbt -> Making Star Schema, Jinja, data quality tests, data documentation
* **Containerization**: Docker and Docker -> Separating Extraction-Load, Modeling and Airflow into Docker containers
* **Orchestration**: Apache Airflow -> Orchestrating the Docker containers to run the pipeline, PostgreSQL backend
* **Visualization**: Power BI -> DAX measures, bookmarks

## Data Model

<img width="720" height="405" alt="investment_portfolio" src="https://github.com/user-attachments/assets/b6768d79-8544-4795-af10-3ae85741119c" />

This Star Schema is the gold level of the **Medallion Structure**. It gets built from the staging tables which are the silver level. The analytics layer is built from this core schema. <br>
**Explore the interactive dbt Documentation and Data Lineage [CLICK HERE](https://peti0505.github.io/portfolio_tracker_elt_pipeline/)**

## Project Structure

<details open>
<summary><b>Click here to collapse the full project structure</b></summary>
   
```text
│   .env.EXAMPLE
│   .gitignore
│   docker-compose.yml
│   gcp_key.EXAMPLE.json
│   portfolio_transactions.EXAMPLE.xlsx
│   portfolio_visualization.pbix
│   profiles.yml
│   README.md
│   
├───airflow
│   │   Dockerfile
│   │   
│   └───dags
│           portfolio_dag.py
│           
├───docs
│       catalog.json
│       index.html
│       manifest.json
│       
├───extract_load
│       config.py
│       Dockerfile
│       extraction.py
│       loading.py
│       main.py
│       requirements.txt
│       
└───modeling
    │   .gitignore
    │   dbt_project.yml
    │   Dockerfile
    │   package-lock.yml
    │   packages.yml
    │   
    ├───.vscode
    │       extensions.json
    │       
    ├───macros
    │       generate_date_id.sql
    │       
    ├───models
    │   ├───marts
    │   │   ├───analytics
    │   │   │       analytics_daily_snapshot.sql
    │   │   │       _analytics.yml
    │   │   │       
    │   │   └───core
    │   │           dim_assets.sql
    │   │           dim_date.sql
    │   │           fact_asset_prices.sql
    │   │           fact_currency_exchange_rate.sql
    │   │           fact_transactions.sql
    │   │           _core_portfolio.yml
    │   │           
    │   └───staging
    │           stg_asset_metadatas.sql
    │           stg_asset_prices.sql
    │           stg_currency_exchange_rate.sql
    │           stg_transactions.sql
    │           _src_raw_tables.yml
    │           _stg_portfolio.yml
    │           
    └───tests
        ├───marts
        │   └───core
        │           assert_dim_assets_uniqueness.sql
        │           assert_fact_transactions_date_not_after_todays_date.sql
        │           
        └───staging
                assert_stg_asset_prices_not_negative.sql
                assert_stg_currency_rates_not_negative.sql
                assert_stg_transactions_asset_amounts_not_negative.sql
                assert_stg_transactions_trade_price_not_negative.sql
```
</details>

### Pipeline features
1. **Data extraction** <br>
The main.py starts the process. The new transactions from the **Google Sheets** get extracted and loaded into **BigQuery**. Only after that will the asset price and FX rate fetching begin. First it fetches the active asset tickers and currencies from BigQuery, only these prices will be fetched from the APIs for **optimization**.

2. **Data Loading** <br>
Every table gets loaded into **Google BigQuery** as **raw tables** for future modeling. If the transaction loading was successful the Google Sheets transactions get cleared to maintain **idempotency**.

3. **Data Modeling** <br>
The staging level is materialized as views so it refreshes instantly. The core **Star Schema** contains **forward filling** for asset prices and FX rates to fill the days where there was no data for it with the **last known price**. 

4. **Data testing** <br>
Data quality tests are being done on every stage of the data in BigQuery. **Generic and singular tests** as well with the help of dbt. This assures that there **won't be any false information downstream**.

5. **Visualization** <br>
The visualization contains the following insights: <br>
**Total value over time** - > The cumulative value of the portfolio over time. <br>
**Top and bottom performers** -> List of the assets that had the highest and lowest earning for the portfolio.
**Asset allocation** -> A treemap to see individual asset earnings and exposure. <br>
**KPIs** -> The asset and FX earning are separated.

6. **Orchestration** <br>
The Airflow gets all the environment variables and the Google Cloud Platform service key to pass on to the containers. The Airflow runs in a container as well, it executes the DAG using the host **Docker Socket**. <br>
If needed the pipeline can be started with Docker Compose as well, but only the Airflow has 
scheduled running.

**Note: The portfolio contains fictional transactions, it doesn't resemble a real portfolio.**

## Visualization

<img width="720" height="405" alt="Képernyőkép 2026-06-03 123355" src="https://github.com/user-attachments/assets/19f2428e-1a95-40c5-ba9e-55f877cb30cb" />

# How to Run

### Prerequisites
* **Docker** and **Docker Compose**.
* A GCP project with a BigQuery dataset and Google Sheets API and Google Drive API enabled.
* A GCP Service account .json key with admin privileges.
* API token for **Tiingo**
* An empty Google Sheets spreadsheet.

### Setup
1. **Clone the repository**
```bash
   git clone https://github.com/phauzer/portfolio_tracker_elt_pipeline.git
   cd portfolio_tracker_elt_pipeline
```

2. **Configure environment variables** <br>
Open the .envEXAMPLE file, write your environment variables according to the instructions then delete the .EXAMPLE from the file name.

3. **Add GCP credentials** <br>
Paste the Google Cloud Platform service key for the project into the gcp_keyEXAMPLE.json file or replace the file. Delete the .EXAMPLE from the file name.

4. **Make Google Sheets for transactions** <br>
* Rename your Google Sheets spreadsheet to "portfolio_transactions" and rename the worksheet to "Transactions" and share this sheet with your GCP service account e-mail.
* Paste the transactions from portfolio_transactions.EXAMPLE.xlsx into the worksheet or write your own transactions following the portfolio_transactions.EXAMPLE.xlsx formatting (note: use tickers that are available in the Tiingo API).

5. **Build the images**
```bash
docker compose --profile portfolio_pipeline build
```
6. **Starting the pipeline** <br>
* If you want to start it with Airflow:
    - ```bash
        docker compose up -d
        ```
    - Navigate to http://localhost:8080 in your browser.
    - Log in to Airflow (default credentials: airflow airflow)
    - Unpause or trigger the DAG to execute the pipeline

* If you want to start it with Docker Compose without scheduling:
    - ```bash
        docker compose --profile portfolio_pipeline up
        ```
7. Visualization <br>
* You can explore the .pbix file in the repository with the original data.
* If you want to refresh it with your own data, connect to your Google BigQuery.
