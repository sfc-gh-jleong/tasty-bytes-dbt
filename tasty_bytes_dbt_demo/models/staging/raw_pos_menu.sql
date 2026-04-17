SELECT *
FROM {{ source('tasty_bytes_dbt_db', 'MENU') }}
