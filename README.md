# Tasty Bytes dbt Demo on Snowflake

A hands-on demo of [dbt Projects on Snowflake](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake) using the Tasty Bytes food truck dataset. Covers staging models, mart tables, Snowpark Python models, custom tests, and CI/CD deployment via the Snowflake CLI.

> **Based on:** [Get started with dbt Projects on Snowflake](https://docs.snowflake.com/en/user-guide/tutorials/dbt-projects-on-snowflake-getting-started-tutorial)

---

## What You'll Build

```
tasty_bytes_dbt_db
├── raw/                        ← Source data (loaded by setup SQL)
│   ├── country
│   ├── franchise
│   ├── location
│   ├── menu
│   ├── truck
│   ├── order_header
│   ├── order_detail
│   └── customer_loyalty
│
├── dev/                        ← dbt dev environment (materialized below)
└── prod/                       ← dbt prod environment (materialized below)
    ├── staging/ (views)
    │   ├── raw_pos_country
    │   ├── raw_pos_franchise
    │   ├── raw_pos_location
    │   ├── raw_pos_menu
    │   ├── raw_pos_truck
    │   ├── raw_pos_order_header
    │   ├── raw_pos_order_detail
    │   └── raw_customer_customer_loyalty
    └── marts/ (tables)
        ├── orders                        ← Full enriched order fact
        ├── customer_loyalty_metrics      ← Total spend per customer
        ├── sales_data_by_truck           ← Monthly revenue by truck brand
        └── sales_metrics_by_location     ← Location sales (Snowpark Python)
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Snowflake account | ACCOUNTADMIN or equivalent setup privileges |
| [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation/installation) | `snow --version` to verify |
| Python 3.10+ | For dbt and Snowpark models |
| dbt-snowflake | `pip install dbt-snowflake` |

Enable the dbt Projects feature flag in the CLI:

```bash
export SNOWFLAKE_CLI_FEATURES_ENABLE_DBT=true
```

---

## Step 1 — Load Source Data

Run the setup script in Snowsight or via CLI. This creates the `tasty_bytes_dbt_db` database with `raw`, `dev`, and `prod` schemas, then loads 8 raw tables from S3.

```sql
-- In Snowsight: open and run setup/tasty_bytes_setup.sql
-- Or via CLI:
snow sql -f tasty_bytes_dbt_demo/setup/tasty_bytes_setup.sql
```

Verify the load:

```sql
SELECT 'tasty_bytes_dbt_db setup is now complete' AS note;
SHOW TABLES IN SCHEMA tasty_bytes_dbt_db.raw;
```

---

## Step 2 — Configure Your Connection

The `profiles.yml` is pre-configured to write to `tasty_bytes_dbt_db`. Update your account, user, and warehouse:

```yaml
# tasty_bytes_dbt_demo/profiles.yml
tasty_bytes:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: '<your-account>'       # e.g. myorg-myaccount
      user: '<your-user>'
      role: sysadmin
      database: tasty_bytes_dbt_db
      schema: dev
      warehouse: M_WAREHOUSE
    prod:
      type: snowflake
      account: '<your-account>'
      user: '<your-user>'
      role: sysadmin
      database: tasty_bytes_dbt_db
      schema: prod
      warehouse: M_WAREHOUSE
```

> **Note:** When using `snow dbt`, connection is handled automatically via your active Snowflake CLI connection — the `profiles.yml` is used for local dbt runs only.

---

## Step 3 — Run Locally with dbt

```bash
cd tasty_bytes_dbt_demo

# Check your connection
dbt debug

# Run all models against dev
dbt run

# Run only staging models
dbt run --select staging

# Run only mart models
dbt run --select marts

# Run a single model
dbt run --select orders

# Run tests
dbt test

# Run tests on a specific model
dbt test --select raw_pos_order_detail

# Generate and serve docs
dbt docs generate && dbt docs serve
```

Expected output after `dbt run`:

```
✓  raw_pos_country          (view)
✓  raw_pos_franchise        (view)
✓  raw_pos_location         (view)
✓  raw_pos_menu             (view)
✓  raw_pos_truck            (view)
✓  raw_pos_order_header     (view)
✓  raw_pos_order_detail     (view)
✓  raw_customer_customer_loyalty  (view)
✓  orders                   (table)
✓  customer_loyalty_metrics (table)
✓  sales_data_by_truck      (table)
✓  sales_metrics_by_location (table)
```

---

## Step 4 — Deploy with Snowflake CLI (Native dbt Projects)

Deploy the project as a native Snowflake dbt project object:

```bash
# Deploy to Snowflake (creates a DBT PROJECT object)
snow dbt deploy DEMO_DBT_PROJECT --source ./tasty_bytes_dbt_demo

# List deployed projects
snow dbt list

# Execute a full run against prod
snow dbt execute DEMO_DBT_PROJECT run --target prod

# Execute a single model
snow dbt execute DEMO_DBT_PROJECT run --target prod --select orders

# Run tests
snow dbt execute DEMO_DBT_PROJECT test --target prod

# Run tests on a specific model
snow dbt execute DEMO_DBT_PROJECT test --target prod --select raw_pos_order_detail
```

---

## Step 5 — Explore the Results

After a successful run, query the mart tables:

```sql
-- Top customers by total spend
SELECT first_name, last_name, country, total_sales
FROM tasty_bytes_dbt_db.dev.customer_loyalty_metrics
ORDER BY total_sales DESC
LIMIT 10;

-- Monthly revenue by truck brand
SELECT truck_brand_name, sales_month, total_revenue, total_orders
FROM tasty_bytes_dbt_db.dev.sales_data_by_truck
ORDER BY sales_month DESC, total_revenue DESC
LIMIT 20;

-- Full enriched orders
SELECT order_id, truck_brand_name, menu_type, primary_city, order_total
FROM tasty_bytes_dbt_db.dev.orders
LIMIT 10;
```

---

## CI/CD with GitHub Actions

The `.github/workflows/deploy_dbt_project.yaml` workflow automatically deploys on every push to `main` using OIDC authentication.

**Required GitHub secrets/variables:**

| Name | Type | Value |
|---|---|---|
| `SNOWFLAKE_ACCOUNT` | Secret | Your Snowflake account identifier |
| `SNOWFLAKE_DATABASE` | Variable | `tasty_bytes_dbt_db` |
| `SNOWFLAKE_SCHEMA` | Variable | `prod` |

The workflow:
1. Installs the Snowflake CLI
2. Tests the connection via OIDC
3. Runs `snow dbt deploy DEMO_DBT_PROJECT`
4. Lists deployed dbt project objects

---

## Project Structure

```
tasty-bytes-dbt/
├── .github/
│   └── workflows/
│       └── deploy_dbt_project.yaml   ← CI/CD pipeline
└── tasty_bytes_dbt_demo/
    ├── dbt_project.yml               ← Project config (staging=view, marts=table)
    ├── profiles.yml                  ← Connection profiles (dev + prod)
    ├── setup/
    │   └── tasty_bytes_setup.sql     ← One-time database + data setup
    ├── models/
    │   ├── staging/
    │   │   ├── __sources.yml         ← Source definitions + column tests
    │   │   └── raw_*.sql             ← Staging views over raw tables
    │   └── marts/
    │       ├── orders.sql            ← Enriched order fact table
    │       ├── customer_loyalty_metrics.sql
    │       ├── sales_data_by_truck.sql
    │       ├── sales_metrics_by_location.py  ← Snowpark Python model
    │       └── orders_spark.py               ← Snowpark Python model
    ├── macros/
    │   └── generate_schema_name.sql  ← Schema routing macro
    ├── tests/
    │   └── generic/
    │       └── test_is_positive_amount.sql   ← Custom generic test
    └── examples/
        └── tasty_bytes_example_query.sql     ← Sample queries
```

---

## Key Concepts Demonstrated

| Concept | Where |
|---|---|
| Source definitions with column tests | `models/staging/__sources.yml` |
| Staging views with `source()` macro | `models/staging/raw_*.sql` |
| Mart tables with `ref()` macro | `models/marts/*.sql` |
| Snowpark Python models | `models/marts/sales_metrics_by_location.py` |
| Custom generic test | `tests/generic/test_is_positive_amount.sql` |
| Schema name override macro | `macros/generate_schema_name.sql` |
| Native Snowflake deployment | `snow dbt deploy` |
| CI/CD with OIDC auth | `.github/workflows/deploy_dbt_project.yaml` |

---

## Resources

- [dbt Projects on Snowflake — Docs](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake)
- [Tutorial: Get started with dbt Projects on Snowflake](https://docs.snowflake.com/en/user-guide/tutorials/dbt-projects-on-snowflake-getting-started-tutorial)
- [Snowflake CLI Reference — snow dbt](https://docs.snowflake.com/en/developer-guide/snowflake-cli/command-reference/dbt)
- [Tasty Bytes Sample Dataset](https://docs.snowflake.com/en/user-guide/sample-data-tasty-bytes)
