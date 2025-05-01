# Nifty 100 Financial Tracker

Track quarterly and yearly earnings of top Nifty 100 companies.

This project gathers financial data for companies listed in the Nifty 100 index from Screener. The data is initially stored in CSV files and then uploaded into PostgreSQL tables for structured analysis.

## Data Source

Financial data is sourced from [Screener](https://www.screener.in/).

## Data Storage

The project utilizes two primary storage methods:

1.  **CSV Files (Intermediate):** Raw data extracted from Screener is first saved into CSV files following a specific format.
2.  **PostgreSQL Database:** The data from the CSV files is then loaded into PostgreSQL tables for efficient querying and analysis.

### CSV File Formatting

1.  **QUARTERLY EARNINGS**
    ```
    SYMBOL,MONTH,YEAR,SALES,EXPENSES,PBT,PAT,EPS
    ```

2.  **ANNUAL EARNINGS**
    ```
    SYMBOL,MONTH,YEAR,SALES,EXPENSES,PBT,PAT,EPS
    ```

## PostgreSQL Database Schema

The database name is `nifty_financial_results`. It contains two tables: `quarters` and `annual`.

### `quarters` Table

Stores quarterly financial data.

| **Column** | **Data Type** | **Constraints** | **Description** |
| :-------------- | :------------ | :---------------------------------- | :-------------------------------------------- |
| `uuid`          | `serial`      | `PRIMARY KEY`, `auto-incrementing`  | Unique identifier for each record             |
| `month`         | `smallint`    | `NOT NULL`, `CHECK (month >= 1 AND month <= 12)` | Month of the reporting quarter (1-12)       |
| `year`          | `smallint`    | `NOT NULL`                          | Year of the reporting quarter                 |
| `security_name` | `varchar(250)`| `NOT NULL`                          | Name of the Nifty 100 company               |
| `metric_name`   | `varchar(15)` | `NOT NULL`                          | Financial metric (Sales, Expenses, PBT, PAT, EPS) |
| `metric_value`  | `real`        | `NOT NULL`                          | Value of the financial metric                 |

```sql
CREATE TABLE quarters (
    uuid serial PRIMARY KEY,
    month smallint NOT NULL CHECK (month >= 1 AND month <= 12),
    year smallint NOT NULL,
    security_name varchar(250) NOT NULL,
    metric_name varchar(15) NOT NULL,
    metric_value real NOT NULL
);
