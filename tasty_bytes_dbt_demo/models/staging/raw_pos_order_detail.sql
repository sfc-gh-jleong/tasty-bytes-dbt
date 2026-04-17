SELECT *
FROM {{ source('tasty_bytes_dbt_db', 'ORDER_DETAIL') }}
